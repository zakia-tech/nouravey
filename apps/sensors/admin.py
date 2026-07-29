from django.contrib import admin

from .models import SensorReading


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ('station_name', 'aqi', 'pm25', 'fetched_at')
    list_filter = ('station_name',)
    readonly_fields = ('fetched_at',)
    actions = ['refresh_from_iqair']

    @admin.action(description='Refresh air quality data from IQAir now')
    def refresh_from_iqair(self, request, queryset):
        from .services import refresh_air_quality
        reading = refresh_air_quality()
        if reading:
            self.message_user(request, f'Successfully refreshed: {reading}')
        else:
            self.message_user(request, 'Failed to fetch air quality data. Check API key and connection.', level='error')
