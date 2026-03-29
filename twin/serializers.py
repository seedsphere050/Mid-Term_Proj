# backend/plants/serializers.py
from rest_framework import serializers

ALL_PLANT_CHOICES = [
    'neem','apple','corn','orange','peach','pepper','potato','strawberry',
    'tomato','snake_plant','tulsi','aloe_vera','christmas_tree','hibiscus',
    'bougainvillea','lavender','peony','hydrangea','onion','garlic',
    'pineapple','oats','pot_marigold','papaya','blue_cornflower','lemon',
    'coffee_tree','wild_carrot','snowdrop','soyabean','english_ivy','hops',
    'lotus','yarrow','feverfew','oleander','oregano','avocado','beetroot',
    'vervain','money_plant','banyan','purple_coneflower','basil','rose',
]

class EnvironmentSerializer(serializers.Serializer):
    environment_type   = serializers.ChoiceField(choices=['indoor','outdoor'],      default='outdoor')
    location_type      = serializers.ChoiceField(choices=['balcony','terrace','ground'], default='ground')
    sunlight           = serializers.ChoiceField(choices=['full_sun','partial_shade','low_light'], default='full_sun')
    watering_frequency = serializers.ChoiceField(choices=['daily','alternate','weekly'], default='daily')
    soil_type          = serializers.ChoiceField(choices=['sandy','loamy','clay'],  default='loamy')
    pot_size           = serializers.ChoiceField(choices=['small','medium','large'],default='medium')

class PlantCreateSerializer(serializers.Serializer):
    plant_name  = serializers.CharField(max_length=100)
    plant_type  = serializers.ChoiceField(choices=ALL_PLANT_CHOICES)
    owner_name  = serializers.CharField(max_length=100, default='Gardener')
    notes       = serializers.CharField(required=False, allow_blank=True, default='')
    environment = EnvironmentSerializer()

class PlantUpdateSerializer(serializers.Serializer):
    environment = EnvironmentSerializer(required=False)
    notes       = serializers.CharField(required=False, allow_blank=True)

class PlantResponseSerializer(serializers.Serializer):
    plant_id           = serializers.CharField()
    plant_name         = serializers.CharField()
    plant_type         = serializers.CharField()
    owner_name         = serializers.CharField()
    planting_date      = serializers.DateTimeField()
    created_at         = serializers.DateTimeField()
    current_stage      = serializers.CharField()
    stage_label        = serializers.CharField()
    health_score       = serializers.FloatField()
    health_label       = serializers.CharField()
    health_color       = serializers.CharField()
    effective_days     = serializers.FloatField()
    real_days          = serializers.FloatField()
    growth_percentage  = serializers.FloatField()
    growth_multiplier  = serializers.FloatField()
    stage_progress     = serializers.FloatField()
    days_to_next_stage = serializers.FloatField()
    condition_scores   = serializers.DictField(child=serializers.FloatField())
    condition_labels   = serializers.DictField(child=serializers.CharField())
    recommendations    = serializers.ListField(child=serializers.CharField())
    visual_profile     = serializers.DictField(child=serializers.CharField())
    environment        = EnvironmentSerializer()
    notes              = serializers.CharField()
