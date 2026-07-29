from django.db import models


CONFIDENCE_CHOICES = [
    ('low', 'Low'),
    ('nominal', 'Nominal'),
    ('high', 'High'),
]


class SatelliteHotspot(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()

    brightness = models.FloatField()
    confidence = models.CharField(max_length=10, choices=CONFIDENCE_CHOICES)

    detected_at = models.DateTimeField()  # actual FIRMS detection time
    fetched_at = models.DateTimeField(auto_now_add=True)  # when pulled it

    def __str__(self):
        return f"Thermal anomaly ({self.confidence}) at {self.latitude:.4f}, {self.longitude:.4f}"

    class Meta:
        ordering = ['-detected_at']
