from django.db import models

# Create your models here.
class Tip(models.Model):
    text = models.TextField()
    video_url = models.URLField()
    category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:50]