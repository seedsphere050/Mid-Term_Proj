from django.db import models

# Create your models here.
class Plant(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='plants/', blank=True, null=True)

    def __str__(self):
        return self.name