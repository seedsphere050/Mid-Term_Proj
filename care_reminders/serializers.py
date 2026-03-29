
# CHANGE: NEW FILE — care_reminders/serializers.py
import datetime
from rest_framework import serializers
from .models import CareReminder, Notification, UserNotificationSettings


class CareReminderSerializer(serializers.ModelSerializer):
    days_until_water  = serializers.SerializerMethodField()
    days_until_fert   = serializers.SerializerMethodField()
    urgency           = serializers.SerializerMethodField()

    class Meta:
        model  = CareReminder
        fields = [
            'id', 'plant_name', 'plant_type', 'notes',
            'base_water_days', 'base_fert_days',
            'next_watering', 'next_fertilize',
            'last_watered', 'last_fertilized',
            'missed_waterings', 'health_score',
            'current_weather',
            'days_until_water', 'days_until_fert', 'urgency',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'health_score']

    def get_days_until_water(self, obj):
        return (obj.next_watering - datetime.date.today()).days

    def get_days_until_fert(self, obj):
        return (obj.next_fertilize - datetime.date.today()).days

    def get_urgency(self, obj):
        d = (obj.next_watering - datetime.date.today()).days
        if d < 0:  return 'overdue'
        if d == 0: return 'today'
        if d <= 2: return 'soon'
        return 'upcoming'


class NotificationSerializer(serializers.ModelSerializer):
    plant_name = serializers.SerializerMethodField()

    class Meta:
        model  = Notification
        fields = ['id', 'plant', 'plant_name', 'category', 'notif_type',
                  'title', 'message', 'is_read', 'sms_sent', 'created_at']

    def get_plant_name(self, obj):
        return obj.plant.plant_name if obj.plant else None


class UserNotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model  = UserNotificationSettings
        # CHANGE: no user field exposed — single-settings model
        fields = ['id', 'sms_enabled', 'phone_number', 'email_enabled',
                  'in_app_enabled', 'weather_location', 'current_weather']
