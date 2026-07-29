from django.db import models

from apps.reports.models import Report, SUBCOUNTY_CHOICES, WARD_CHOICES
from apps.sensors.models import SensorReading
from apps.satellite.models import SatelliteHotspot


SEVERITY_LABEL_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('critical', 'Critical'),
]

PREDICTED_TREND_CHOICES = [
    ('worsening', 'Likely to Worsen'),
    ('stable', 'Likely to Remain Stable'),
    ('improving', 'Likely to Improve'),
    ('insufficient_data', 'Insufficient Data'),
]


class Hotspot(models.Model):
    center_latitude = models.FloatField()
    center_longitude = models.FloatField()
    ward = models.CharField(max_length=50, choices=WARD_CHOICES, blank=True)
    subcounty = models.CharField(max_length=50, choices=SUBCOUNTY_CHOICES, blank=True)

    reports = models.ManyToManyField(Report, related_name='hotspots')
    sensor_readings = models.ManyToManyField(SensorReading, related_name='hotspots', blank=True)
    satellite_hotspots = models.ManyToManyField(SatelliteHotspot, related_name='hotspots', blank=True)

    score = models.FloatField(default=0)
    severity_label = models.CharField(max_length=10, choices=SEVERITY_LABEL_CHOICES, blank=True)
    narrative = models.TextField(blank=True)
    recommended_action = models.CharField(max_length=255, blank=True)

    # 24-hour predictive forecast
    predicted_trend = models.CharField(max_length=20, choices=PREDICTED_TREND_CHOICES, blank=True)
    prediction_confidence = models.FloatField(default=0.0)
    prediction_rationale = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Hotspot in {self.get_ward_display() or 'Unknown'} — {self.get_severity_label_display() or 'unscored'}"

    class Meta:
        ordering = ['-score']
