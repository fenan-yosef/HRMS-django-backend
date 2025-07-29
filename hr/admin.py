from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department, PerformanceReview, Attendance
from .models import PasswordResetOTP

class CustomUserAdmin(UserAdmin):
    ordering = ['email']  # Update 'username' to 'email' or the correct field

# Register the custom user model
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Department)
admin.site.register(PerformanceReview)
admin.site.register(Attendance)
admin.site.register(PasswordResetOTP)
