from django.contrib import admin
from .models import LeaveRequest

# Register LeaveRequest model
@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'start_date', 'end_date', 'status', 'applied_date')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'reason')
