# CHANGE: NEW FILE — care_reminders/models.py
# Django ORM models for care reminders, notifications, and SMS settings.
# Uses SQLite (Django default) — separate from MongoDB used by Digital Twin.
# No authentication required — consistent with the Digital Twin's no-login design.

from django.db import models

# CHANGE: all 45 plants from the Digital Twin
PLANT_TYPE_CHOICES = [
    ('neem','Neem'),('apple','Apple'),('corn','Corn'),('orange','Orange'),
    ('peach','Peach'),('pepper','Pepper'),('potato','Potato'),
    ('strawberry','Strawberry'),('tomato','Tomato'),('snake_plant','Snake Plant'),
    ('tulsi','Tulsi'),('aloe_vera','Aloe Vera'),('christmas_tree','Christmas Tree'),
    ('hibiscus','Hibiscus'),('bougainvillea','Bougainvillea'),('lavender','Lavender'),
    ('peony','Peony'),('hydrangea','Hydrangea'),('onion','Onion'),('garlic','Garlic'),
    ('pineapple','Pineapple'),('oats','Oats'),('pot_marigold','Pot Marigold'),
    ('papaya','Papaya'),('blue_cornflower','Blue Cornflower'),('lemon','Lemon'),
    ('coffee_tree','Coffee Tree'),('wild_carrot','Wild Carrot'),('snowdrop','Snowdrop'),
    ('soyabean','Soyabean'),('english_ivy','English Ivy'),('hops','Hops'),
    ('lotus','Lotus'),('yarrow','Yarrow'),('feverfew','Feverfew'),
    ('oleander','Oleander'),('oregano','Oregano'),('avocado','Avocado'),
    ('beetroot','Beetroot'),('vervain','Vervain'),('money_plant','Money Plant'),
    ('banyan','Banyan'),('purple_coneflower','Purple Coneflower'),
    ('basil','Basil'),('rose','Rose'),('custom','Custom / Other'),
]

WEATHER_CHOICES = [
    ('sunny','Sunny'),('cloudy','Cloudy'),('rainy','Rainy'),
    ('hot','Hot'),('cold','Cold'),
]


class CareReminder(models.Model):
    """
    One record per plant being tracked for care reminders.
    CHANGE: No user FK — single-user app, consistent with Digital Twin.
    CHANGE: digital_twin_plant_id optionally links to MongoDB plant_profiles.
    """
    # Link to Digital Twin (optional)
    digital_twin_plant_id = models.CharField(
        max_length=64, blank=True, default='',
        help_text='plant_id from MongoDB plant_profiles — links to a digital twin'
    )

    plant_name        = models.CharField(max_length=120)
    plant_type        = models.CharField(max_length=40, choices=PLANT_TYPE_CHOICES, default='custom')
    notes             = models.TextField(blank=True, default='')

    # Schedule — days between care actions
    base_water_days   = models.PositiveSmallIntegerField(default=5)
    base_fert_days    = models.PositiveSmallIntegerField(default=30)

    # Next care dates (recalculated after each action + weather change)
    next_watering     = models.DateField()
    next_fertilize    = models.DateField()

    # History
    last_watered      = models.DateTimeField(null=True, blank=True)
    last_fertilized   = models.DateTimeField(null=True, blank=True)
    missed_waterings  = models.PositiveSmallIntegerField(default=0)

    # Health 0–100
    health_score      = models.SmallIntegerField(default=100)

    # Current weather affecting this plant's schedule
    current_weather   = models.CharField(max_length=20, choices=WEATHER_CHOICES, default='cloudy')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_watering']

    def __str__(self):
        return f'{self.plant_name} ({self.plant_type})'


class UserNotificationSettings(models.Model):
    """
    Global SMS/notification settings — single record (pk=1).
    CHANGE: No user FK — accessed via get_or_create(pk=1).
    """
    sms_enabled      = models.BooleanField(default=False)
    phone_number     = models.CharField(max_length=20, blank=True, default='',
                       help_text='With country code, e.g. +919876543210')
    email_enabled    = models.BooleanField(default=False)
    in_app_enabled   = models.BooleanField(default=True)
    weather_location = models.CharField(max_length=120, blank=True, default='',
                       help_text='City name or lat,lon for auto weather fetch')
    current_weather  = models.CharField(max_length=20, choices=WEATHER_CHOICES, default='cloudy')
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Notification Settings'

    def __str__(self):
        return f'Settings (sms={self.sms_enabled}, phone={self.phone_number})'


class Notification(models.Model):
    """
    In-app notification record. Shown in the Notifications page.
    Created by: daily check, watering/fertilizing actions.
    sms_sent=True = SMS was already sent for this alert.
    """
    CATEGORY_CHOICES = [
        ('urgent','Urgent'),
        ('upcoming','Upcoming'),
        ('informational','Informational'),
    ]
    TYPE_CHOICES = [
        ('watering','Watering'),
        ('fertilize','Fertilize'),
        ('stress','Plant Stress'),
        ('general','General'),
    ]

    # CHANGE: plant is optional — allows general notifications with no plant attached
    plant      = models.ForeignKey(
        CareReminder, on_delete=models.CASCADE,
        related_name='notifications', null=True, blank=True
    )
    category   = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    notif_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    sms_sent   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.category}] {self.title}'
