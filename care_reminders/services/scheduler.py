# care_reminders/services/scheduler.py
# CHANGE: Completely rewritten — scheduler now reads watering and fertilizing
# status DIRECTLY from MongoDB (Digital Twin plant_profiles collection),
# not from a separate SQLite schedule. This ensures Care Reminders and
# Digital Twin always show the same data.
#
# Flow:
#   run_daily_check()
#     → fetches all plants from MongoDB
#     → for each plant, checks last_watered / last_fertilized timestamps
#     → computes days since last watered vs expected watering_frequency
#     → generates Notification records (in SQLite via Django ORM)
#     → fires SMS if critical (3+ days overdue)

import datetime
import logging
from .sms import send_critical_sms

logger = logging.getLogger(__name__)

# ── Watering frequency → expected days between waterings ─────────────────────
WATERING_FREQ_DAYS = {
    'daily':     1,
    'alternate': 2,
    'weekly':    7,
}

# ── Health score helpers ──────────────────────────────────────────────────────

def calculate_health_score(plant) -> int:
    """
    Returns 0–100. Used for SQLite-backed CareReminder records.
    Penalties: overdue watering, overdue fertilizing, missed waterings.
    """
    today = datetime.date.today()
    score = 100
    water_diff = (plant.next_watering - today).days
    fert_diff  = (plant.next_fertilize - today).days
    if water_diff < 0:
        score -= min(40, abs(water_diff) * 8)
    elif water_diff == 0:
        score -= 10
    if fert_diff < 0:
        score -= min(20, abs(fert_diff) * 4)
    score -= min(30, plant.missed_waterings * 5)
    return max(0, min(100, score))


def mark_watered(plant) -> None:
    """Record watering in SQLite, reset missed counter, recalculate schedule."""
    from django.utils import timezone
    plant.last_watered     = timezone.now()
    plant.missed_waterings = 0
    from .weather import calc_adjusted_days
    adj = calc_adjusted_days(plant.base_water_days, getattr(plant, 'current_weather', 'cloudy'))
    plant.next_watering = datetime.date.today() + datetime.timedelta(days=adj)
    plant.health_score  = calculate_health_score(plant)
    plant.save()


def mark_fertilized(plant) -> None:
    """Record fertilizing in SQLite, push next fertilize date."""
    from django.utils import timezone
    plant.last_fertilized = timezone.now()
    plant.next_fertilize  = datetime.date.today() + datetime.timedelta(days=plant.base_fert_days)
    plant.save(update_fields=['last_fertilized', 'next_fertilize', 'updated_at'])


def reschedule_plant(plant, condition: str) -> None:
    """Recalculate next_watering from last_watered + weather multiplier."""
    from .weather import calc_adjusted_days
    adj   = calc_adjusted_days(plant.base_water_days, condition)
    start = plant.last_watered.date() if plant.last_watered else datetime.date.today()
    plant.next_watering = start + datetime.timedelta(days=adj)
    plant.health_score  = calculate_health_score(plant)
    plant.save(update_fields=['next_watering', 'health_score', 'updated_at'])


def reschedule_all_for_weather(condition: str) -> int:
    """Reschedule ALL SQLite reminders when user changes weather mode."""
    from ..models import CareReminder
    updated = 0
    for plant in CareReminder.objects.all():
        plant.current_weather = condition
        reschedule_plant(plant, condition)
        updated += 1
    return updated


# ── MongoDB helpers ───────────────────────────────────────────────────────────

def _get_mongo_col(col_name):
    """Open MongoDB collection using MONGO_URI"""
    import pymongo
    from django.conf import settings as djsettings

    client = pymongo.MongoClient(djsettings.MONGO_URI)
    db = client[djsettings.MONGO_DB_NAME]
    return db[col_name]

def _days_since(iso_or_dt) -> int:
    """Return how many days have elapsed since a datetime. None → 9999."""
    if iso_or_dt is None:
        return 9999
    try:
        if isinstance(iso_or_dt, datetime.datetime):
            dt = iso_or_dt
        else:
            dt = datetime.datetime.fromisoformat(str(iso_or_dt).replace('Z', '+00:00'))
        # Make naive UTC for subtraction
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return (datetime.datetime.utcnow() - dt).days
    except Exception:
        return 9999


def _expected_water_days(env: dict) -> int:
    """Map watering_frequency from Digital Twin environment to days."""
    freq = (env or {}).get('watering_frequency', 'alternate')
    return WATERING_FREQ_DAYS.get(freq, 2)


# ── Main daily check — reads FROM MongoDB ────────────────────────────────────

def run_daily_check() -> dict:
    """
    CHANGE: Called once per day (management command, cron, or POST /api/care/run-check/).
    Reads ALL plants from MongoDB Digital Twin, checks their last_watered and
    last_fertilized timestamps, and creates Notification records accordingly.
    SMS fires for plants that are 3+ days overdue for watering.

    No separate SQLite CareReminder records needed — MongoDB is the source of truth.
    Returns a summary dict with counts.
    """
    from ..models import Notification, UserNotificationSettings

    today  = datetime.datetime.utcnow().date()
    stats  = {'urgent': 0, 'upcoming': 0, 'info': 0, 'sms_sent': 0, 'total': 0, 'errors': []}

    # ── Get SMS settings ──────────────────────────────────────────────────────
    try:
        sms_settings = UserNotificationSettings.objects.first()
    except Exception:
        sms_settings = None

    # ── Fetch all Digital Twin plants from MongoDB ────────────────────────────
    try:
        col   = _get_mongo_col('plant_profiles')
        plants = list(col.find({}))
    except Exception as e:
        logger.error(f'MongoDB connection failed in run_daily_check: {e}')
        stats['errors'].append(f'MongoDB error: {e}')
        return stats

    for plant_doc in plants:
        stats['total'] += 1
        plant_name = plant_doc.get('plant_name', 'Unknown Plant')
        plant_id   = plant_doc.get('plant_id', str(plant_doc.get('_id', '')))
        env        = plant_doc.get('environment', {})

        # ── Watering check ────────────────────────────────────────────────────
        last_watered    = plant_doc.get('last_watered')
        days_since_water = _days_since(last_watered)
        expected_days   = _expected_water_days(env)
        water_overdue_by = days_since_water - expected_days   # positive = overdue

        if days_since_water == 9999:
            # Never watered
            Notification.objects.create(
                plant      = None,
                category   = 'urgent',
                notif_type = 'watering',
                title      = f'💧 {plant_name} has never been watered!',
                message    = (
                    f'Your Digital Twin plant "{plant_name}" has no recorded watering. '
                    f'Go to Digital Twin → Care tab → Water Now.'
                ),
            )
            stats['urgent'] += 1

        elif water_overdue_by > 0:
            # Overdue
            category = 'urgent'
            title    = f'⚠️ {plant_name} is overdue for watering!'
            message  = (
                f'"{plant_name}" was last watered {days_since_water} day(s) ago. '
                f'Expected every {expected_days} day(s). '
                f'It is {water_overdue_by} day(s) overdue. '
                f'Go to Digital Twin → Care tab to water it.'
            )
            Notification.objects.create(
                plant=None, category=category, notif_type='watering',
                title=title, message=message,
            )
            stats['urgent'] += 1

            # ── SMS for 1+ days overdue ───────────────────────────────────────
            if water_overdue_by >= 1 and sms_settings and sms_settings.sms_enabled and sms_settings.phone_number:
                sent = send_critical_sms(sms_settings.phone_number, message)
                if sent:
                    stats['sms_sent'] += 1
                    logger.info(f'SMS sent for {plant_name} (overdue {water_overdue_by}d)')

        elif water_overdue_by == 0 or days_since_water == expected_days - 1:
            # Due today or tomorrow
            Notification.objects.create(
                plant=None, category='upcoming', notif_type='watering',
                title=f'💧 Water {plant_name} today',
                message=(
                    f'"{plant_name}" is due for watering today (every {expected_days} day(s)). '
                    f'Last watered {days_since_water} day(s) ago.'
                ),
            )
            stats['upcoming'] += 1

        # ── Fertilizing check ─────────────────────────────────────────────────
        last_fertilized      = plant_doc.get('last_fertilized')
        days_since_fertilize = _days_since(last_fertilized)
        # Default: fertilize every 30 days (good for most plants)
        fert_every = 30

        if last_fertilized is None:
            # Never fertilized — gentle reminder, not urgent
            Notification.objects.create(
                plant=None, category='upcoming', notif_type='fertilize',
                title=f'🌿 {plant_name} has never been fertilized',
                message=(
                    f'"{plant_name}" has no fertilization record. '
                    f'Consider fertilizing for better growth.'
                ),
            )
            stats['upcoming'] += 1
        elif days_since_fertilize >= fert_every:
            overdue_fert = days_since_fertilize - fert_every
            category = 'urgent' if overdue_fert >= 7 else 'upcoming'
            Notification.objects.create(
                plant=None, category=category, notif_type='fertilize',
                title=f'🌿 {"Overdue: f" if overdue_fert >= 7 else "F"}ertilize {plant_name}',
                message=(
                    f'"{plant_name}" was last fertilized {days_since_fertilize} day(s) ago '
                    f'(recommended every {fert_every} days). '
                    f'Go to Digital Twin → Care tab to log fertilizing.'
                ),
            )
            if overdue_fert >= 7:
                stats['urgent'] += 1
            else:
                stats['upcoming'] += 1
        elif days_since_fertilize >= fert_every - 3:
            # Coming up in 3 days
            Notification.objects.create(
                plant=None, category='upcoming', notif_type='fertilize',
                title=f'🌿 Fertilize {plant_name} soon',
                message=(
                    f'"{plant_name}" is due for fertilizing in about '
                    f'{fert_every - days_since_fertilize} day(s).'
                ),
            )
            stats['upcoming'] += 1

    logger.info(f'Daily check complete (from MongoDB): {stats}')
    return stats
