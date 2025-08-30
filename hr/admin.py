from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, PerformanceReview, Attendance, Complaint
from department.models import Department
from .models import PasswordResetOTP

class CustomUserAdmin(UserAdmin):
    ordering = ['email']  # Update 'username' to 'email' or the correct field

# Register the custom user model
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(PerformanceReview)
admin.site.register(Attendance)
admin.site.register(PasswordResetOTP)
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "subject", "created_by", "target_user", "status", "created_at")
    list_filter = ("type", "status")
    search_fields = ("subject", "description", "created_by__email", "target_user__email")
