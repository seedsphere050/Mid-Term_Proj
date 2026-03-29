# care_reminders/urls.py
# CHANGE: Added sync-from-dt/ endpoint that reads from MongoDB Digital Twin
from django.urls import path
from .views import (
    CareReminderListCreateView,
    CareReminderDetailView,
    MarkWateredView,
    MarkFertilizedView,
    WeatherRescheduleView,
    NotificationListView,
    MarkNotificationReadView,
    MarkAllReadView,
    NotificationSettingsView,
    CareDashboardView,
    RunDailyCheckView,
    SyncFromDigitalTwinView,   # CHANGE: new
)

urlpatterns = [
    # Care reminders CRUD
    path('reminders/',          CareReminderListCreateView.as_view(), name='care-list'),
    path('reminders/<int:pk>/', CareReminderDetailView.as_view(),     name='care-detail'),

    # Care actions
    path('reminders/<int:pk>/water/',     MarkWateredView.as_view(),    name='care-water'),
    path('reminders/<int:pk>/fertilize/', MarkFertilizedView.as_view(), name='care-fertilize'),

    # CHANGE: sync care status directly from MongoDB Digital Twin
    path('sync-from-dt/', SyncFromDigitalTwinView.as_view(), name='care-sync-dt'),

    # Weather reschedule
    path('weather/', WeatherRescheduleView.as_view(), name='care-weather'),

    # Notifications
    path('notifications/',               NotificationListView.as_view(),      name='notif-list'),
    path('notifications/<int:pk>/read/', MarkNotificationReadView.as_view(),   name='notif-read'),
    path('notifications/read-all/',      MarkAllReadView.as_view(),            name='notif-read-all'),

    # Settings (SMS phone number, toggles) — persisted in SQLite
    path('settings/', NotificationSettingsView.as_view(), name='care-settings'),

    # Dashboard summary
    path('dashboard/', CareDashboardView.as_view(), name='care-dashboard'),

    # Manual daily check — reads MongoDB, creates Notifications
    path('run-check/', RunDailyCheckView.as_view(), name='care-run-check'),
]
