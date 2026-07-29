from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'ward', 'subcounty', 'pollution_type', 'severity', 'status', 'submitted_at')
    list_filter = ('subcounty', 'ward', 'pollution_type', 'status', 'input_type')
    search_fields = ('text_description', 'likely_cause')
    readonly_fields = ('submitted_at', 'status_updated_at', 'subcounty')
