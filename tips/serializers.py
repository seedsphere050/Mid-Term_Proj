from rest_framework import serializers

class TipSerializer(serializers.Serializer):
    tip_no = serializers.CharField()
    category = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    video = serializers.URLField()