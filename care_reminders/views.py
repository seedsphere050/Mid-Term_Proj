from django.shortcuts import render

# Create your views here.
# care_reminders/views.py
# CHANGE: Updated — Care Reminders now reads watering/fertilizing status
# directly from MongoDB (Digital Twin). Settings (phone number, SMS toggle)
# are persisted in SQLite via Django ORM so they survive page refreshes.

import datetime
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import CareReminder, Notification, UserNotificationSettings
from .serializers import (
    CareReminderSerializer,
    NotificationSerializer,
    UserNotificationSettingsSerializer,
)
from .services.scheduler import (
    mark_watered, mark_fertilized,
    reschedule_all_for_weather,
    run_daily_check, calculate_health_score,
    _get_mongo_col,
)
from .services.weather import calc_adjusted_days, fetch_weather
logger = logging.getLogger(__name__)
def _ist_now():
    from datetime import timezone, timedelta
    return datetime.datetime.now(tz=timezone(timedelta(hours=5, minutes=30))).isoformat()


# ── Care Reminders CRUD ───────────────────────────────────────────────────────

class CareReminderListCreateView(APIView):
    """
    GET  /api/care/reminders/   — list all SQLite reminders
    POST /api/care/reminders/   — create a new reminder linked to a DT plant
    """

    def get(self, request):
        reminders = CareReminder.objects.all()
        urgency_filter = request.query_params.get('urgency')
        if urgency_filter:
            today = datetime.date.today()
            if urgency_filter == 'overdue':
                reminders = reminders.filter(next_watering__lt=today)
            elif urgency_filter == 'today':
                reminders = reminders.filter(next_watering=today)
            elif urgency_filter == 'soon':
                reminders = reminders.filter(
                    next_watering__gt=today,
                    next_watering__lte=today + datetime.timedelta(days=2)
                )
            elif urgency_filter == 'upcoming':
                reminders = reminders.filter(
                    next_watering__gt=today + datetime.timedelta(days=2)
                )
        serializer = CareReminderSerializer(reminders, many=True)
        return Response({'reminders': serializer.data, 'count': reminders.count()})

    def post(self, request):
        data = request.data.copy()
        base_water = int(data.get('base_water_days', 5))
        base_fert  = int(data.get('base_fert_days', 30))
        weather    = data.get('current_weather', 'cloudy')
        adj_water  = calc_adjusted_days(base_water, weather)

        data['next_watering']  = (datetime.date.today() + datetime.timedelta(days=adj_water)).isoformat()
        data['next_fertilize'] = (datetime.date.today() + datetime.timedelta(days=base_fert)).isoformat()

        serializer = CareReminderSerializer(data=data)
        if serializer.is_valid():
            reminder = serializer.save()
            reminder.health_score = calculate_health_score(reminder)
            reminder.save(update_fields=['health_score'])
            return Response(CareReminderSerializer(reminder).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CareReminderDetailView(APIView):
    def _get(self, pk):
        try:
            return CareReminder.objects.get(pk=pk)
        except CareReminder.DoesNotExist:
            return None

    def get(self, request, pk):
        r = self._get(pk)
        if not r:
            return Response({'error': 'Not found'}, status=404)
        return Response(CareReminderSerializer(r).data)

    def patch(self, request, pk):
        r = self._get(pk)
        if not r:
            return Response({'error': 'Not found'}, status=404)
        serializer = CareReminderSerializer(r, data=request.data, partial=True)
        if serializer.is_valid():
            reminder = serializer.save()
            reminder.health_score = calculate_health_score(reminder)
            reminder.save(update_fields=['health_score'])
            return Response(CareReminderSerializer(reminder).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        r = self._get(pk)
        if not r:
            return Response({'error': 'Not found'}, status=404)
        r.delete()
        return Response({'deleted': True}, status=status.HTTP_204_NO_CONTENT)


# ── Care Actions ──────────────────────────────────────────────────────────────

class MarkWateredView(APIView):
    """POST /api/care/reminders/<id>/water/"""

    def post(self, request, pk):
        try:
            reminder = CareReminder.objects.get(pk=pk)
        except CareReminder.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        mark_watered(reminder)
        Notification.objects.create(
            plant=reminder, category='informational', notif_type='watering',
            title=f'💧 {reminder.plant_name} watered',
            message=f'{reminder.plant_name} was watered. Next watering: {reminder.next_watering}.',
        )
        return Response({
            'message': 'Watered!',
            'next_watering': reminder.next_watering.isoformat(),
            'health_score': reminder.health_score,
            'ist_time': _ist_now(),
        })


class MarkFertilizedView(APIView):
    """POST /api/care/reminders/<id>/fertilize/"""

    def post(self, request, pk):
        try:
            reminder = CareReminder.objects.get(pk=pk)
        except CareReminder.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        mark_fertilized(reminder)
        Notification.objects.create(
            plant=reminder, category='informational', notif_type='fertilize',
            title=f'🌿 {reminder.plant_name} fertilized',
            message=f'{reminder.plant_name} was fertilized. Next: {reminder.next_fertilize}.',
        )
        return Response({
            'message': 'Fertilized!',
            'next_fertilize': reminder.next_fertilize.isoformat(),
            'ist_time': _ist_now(),
        })


# ── CHANGE: Sync from Digital Twin ───────────────────────────────────────────
# GET /api/care/sync-from-dt/
# Reads all MongoDB plants and returns their watering/fertilizing status
# so the frontend can show accurate alert state without a separate schedule.

class SyncFromDigitalTwinView(APIView):
    """
    GET /api/care/sync-from-dt/
    CHANGE: Returns watering and fertilizing status for every Digital Twin
    plant directly from MongoDB. Frontend uses this to show alerts.
    No SQLite CareReminder record needed.
    """

    WATERING_FREQ_DAYS = {'daily': 1, 'alternate': 2, 'weekly': 7}

    def get(self, request):
        try:
            col = _get_mongo_col('plant_profiles')
            plants = list(col.find({}))
        except Exception as e:
            return Response({'error': f'MongoDB error: {e}'}, status=503)

        now   = datetime.datetime.utcnow()
        today = now.date()
        results = []

        for doc in plants:
            plant_id   = doc.get('plant_id', str(doc.get('_id', '')))
            plant_name = doc.get('plant_name', 'Unknown')
            plant_type = doc.get('plant_type', '')
            env        = doc.get('environment', {})
            stage      = doc.get('current_stage', '')  # may not be in doc directly

            # ── Watering ──────────────────────────────────────────────────────
            last_watered_raw = doc.get('last_watered')
            freq  = env.get('watering_frequency', 'alternate')
            freq_days = self.WATERING_FREQ_DAYS.get(freq, 2)

            if last_watered_raw is None:
                days_since_water = None
                water_overdue_by = None
                water_status     = 'never'
            else:
                lw = last_watered_raw
                if isinstance(lw, str):
                    lw = datetime.datetime.fromisoformat(lw.replace('Z', '+00:00'))
                if lw.tzinfo is not None:
                    lw = lw.replace(tzinfo=None)
                days_since_water = (now - lw).days
                water_overdue_by = max(0, days_since_water - freq_days)
                if water_overdue_by > 0:
                    water_status = 'overdue'
                elif days_since_water >= freq_days - 1:
                    water_status = 'due_today'
                else:
                    water_status = 'ok'

            # ── Fertilizing ───────────────────────────────────────────────────
            last_fert_raw = doc.get('last_fertilized')
            fert_every    = 30  # days

            if last_fert_raw is None:
                days_since_fert = None
                fert_status     = 'never'
            else:
                lf = last_fert_raw
                if isinstance(lf, str):
                    lf = datetime.datetime.fromisoformat(lf.replace('Z', '+00:00'))
                if lf.tzinfo is not None:
                    lf = lf.replace(tzinfo=None)
                days_since_fert = (now - lf).days
                if days_since_fert >= fert_every:
                    fert_status = 'overdue'
                elif days_since_fert >= fert_every - 3:
                    fert_status = 'due_soon'
                else:
                    fert_status = 'ok'

            results.append({
                'plant_id':          plant_id,
                'plant_name':        plant_name,
                'plant_type':        plant_type,
                # Watering
                'watering_freq':     freq,
                'watering_freq_days': freq_days,
                'last_watered':      last_watered_raw.isoformat() if isinstance(last_watered_raw, datetime.datetime) else last_watered_raw,
                'days_since_water':  days_since_water,
                'water_overdue_by':  water_overdue_by,
                'water_status':      water_status,
                # Fertilizing
                'last_fertilized':   last_fert_raw.isoformat() if isinstance(last_fert_raw, datetime.datetime) else last_fert_raw,
                'days_since_fert':   days_since_fert,
                'fert_every_days':   fert_every,
                'fert_status':       fert_status,
            })

        # Sort: overdue first, then due_today, then ok
        priority = {'overdue': 0, 'never': 1, 'due_today': 2, 'due_soon': 3, 'ok': 4}
        results.sort(key=lambda x: (
            priority.get(x['water_status'], 5),
            priority.get(x['fert_status'], 5),
        ))

        urgent_count   = sum(1 for r in results if r['water_status'] in ('overdue', 'never') or r['fert_status'] == 'overdue')
        upcoming_count = sum(1 for r in results if r['water_status'] == 'due_today' or r['fert_status'] == 'due_soon')

        return Response({
            'plants': results,
            'total':  len(results),
            'urgent_count':   urgent_count,
            'upcoming_count': upcoming_count,
        })


# ── Weather reschedule ────────────────────────────────────────────────────────

class WeatherRescheduleView(APIView):
    def post(self, request):
        condition = request.data.get('condition')
        location  = request.data.get('location', '')
        weather_data = None
        if not condition and location:
            weather_data = fetch_weather(location)
            condition    = weather_data.get('condition', 'cloudy')
            settings_obj, _ = UserNotificationSettings.objects.get_or_create(pk=1)
            settings_obj.weather_location = location
            settings_obj.current_weather  = condition
            settings_obj.save()
        if not condition:
            return Response({'error': 'Provide condition or location'}, status=400)
        updated = reschedule_all_for_weather(condition)
        resp = {'condition': condition, 'plants_rescheduled': updated}
        if weather_data:
            resp.update({'temp_c': weather_data.get('temp_c'), 'humidity': weather_data.get('humidity')})
        return Response(resp)


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationListView(APIView):
    """GET /api/care/notifications/?unread=true&limit=50"""

    def get(self, request):
        qs = Notification.objects.all()
        if request.query_params.get('unread') == 'true':
            qs = qs.filter(is_read=False)
        limit = int(request.query_params.get('limit', 50))
        qs = qs[:limit]
        serializer = NotificationSerializer(qs, many=True)
        unread_count = Notification.objects.filter(is_read=False).count()
        return Response({
            'notifications': serializer.data,
            'unread_count':  unread_count,
        })


class MarkNotificationReadView(APIView):
    """POST /api/care/notifications/<id>/read/"""

    def post(self, request, pk):
        try:
            n = Notification.objects.get(pk=pk)
            n.is_read = True
            n.save(update_fields=['is_read'])
            return Response({'status': 'ok'})
        except Notification.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)


class MarkAllReadView(APIView):
    """POST /api/care/notifications/read-all/"""

    def post(self, request):
        updated = Notification.objects.filter(is_read=False).update(is_read=True)
        return Response({'marked_read': updated})


# ── Settings ──────────────────────────────────────────────────────────────────

class NotificationSettingsView(APIView):
    """
    GET   /api/care/settings/   — returns phone number, SMS toggle etc.
    PATCH /api/care/settings/   — saves phone number, SMS toggle
    CHANGE: settings are persisted in SQLite so they survive page refresh.
    Phone number defaults to the logged-in user's number if provided.
    """

    def _settings(self):
        obj, _ = UserNotificationSettings.objects.get_or_create(pk=1)
        return obj

    def get(self, request):
        return Response(UserNotificationSettingsSerializer(self._settings()).data)

    def patch(self, request):
        settings_obj = self._settings()
        serializer   = UserNotificationSettingsSerializer(settings_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            if 'current_weather' in request.data:
                reschedule_all_for_weather(request.data['current_weather'])
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


# ── Dashboard summary ─────────────────────────────────────────────────────────

class CareDashboardView(APIView):
    """GET /api/care/dashboard/"""

    def get(self, request):
        today   = datetime.date.today()
        plants  = CareReminder.objects.all()
        overdue = plants.filter(next_watering__lt=today).count()
        due_today = plants.filter(next_watering=today).count()
        upcoming  = plants.filter(
            next_watering__gt=today,
            next_watering__lte=today + datetime.timedelta(days=3)
        ).count()
        healthy = sum(1 for p in plants if p.health_score >= 80)
        unread  = Notification.objects.filter(is_read=False).count()
        return Response({
            'total_plants':         plants.count(),
            'overdue':              overdue,
            'due_today':            due_today,
            'upcoming_3_days':      upcoming,
            'healthy':              healthy,
            'unread_notifications': unread,
        })


# ── Manual daily check ────────────────────────────────────────────────────────

class RunDailyCheckView(APIView):
    """
    POST /api/care/run-check/
    CHANGE: now reads from MongoDB Digital Twin plants and creates
    Notification records based on actual last_watered / last_fertilized timestamps.
    Call this once a day (cron/Task Scheduler) or manually.
    """

    def post(self, request):
        stats = run_daily_check()
        return Response({
            'message':  'Daily check complete (read from Digital Twin MongoDB)',
            'stats':    stats,
            'ist_time': _ist_now(),
        })
