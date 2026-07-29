from django.contrib import admin

from .models import SatelliteHotspot


@admin.register(SatelliteHotspot)
class SatelliteHotspotAdmin(admin.ModelAdmin):
    list_display = ('latitude', 'longitude', 'brightness', 'confidence', 'detected_at')
    list_filter = ('confidence',)
    readonly_fields = ('fetched_at',)
