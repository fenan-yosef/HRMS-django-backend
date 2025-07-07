from django.contrib import admin
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'job_title', 'department', 'is_active')
    list_filter = ('department', 'is_active')
    search_fields = ('first_name', 'last_name', 'email', 'job_title')