from django.contrib import admin

from .models import Hotspot


@admin.register(Hotspot)
class HotspotAdmin(admin.ModelAdmin):
    list_display = ('id', 'ward', 'severity_label', 'score', 'is_active', 'updated_at')
    list_filter = ('subcounty', 'ward', 'severity_label', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('reports', 'sensor_readings', 'satellite_hotspots')
