from django.contrib import admin
from .models import EmployeeProfile

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "job_title", "supervisor", "start_date", "end_date", "deleted_at")
    list_filter = ("start_date", "end_date")
    search_fields = ("user__email", "user__first_name", "user__last_name", "job_title")
