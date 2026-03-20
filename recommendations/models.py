# recommendations/models.py

from django.db import models

class Plant(models.Model):
    name = models.CharField(max_length=100)

    min_temp = models.FloatField()
    max_temp = models.FloatField()

    soil_type = models.JSONField()      # ["Red", "Black"]
    season = models.JSONField()         # ["Summer", "Spring"]
    rainfall = models.JSONField()       # ["Low", "Moderate"]
    humidity = models.JSONField()       # ["Low", "Medium"]
    sunlight = models.JSONField()       # ["Full Sun"]

    def __str__(self):
        return self.name