from django.db import models


class SensorReading(models.Model):
    station_name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

    aqi = models.IntegerField()
    pm25 = models.FloatField(null=True, blank=True)

    fetched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.station_name} — AQI {self.aqi} ({self.fetched_at:%Y-%m-%d %H:%M})"

    class Meta:
        ordering = ['-fetched_at']
