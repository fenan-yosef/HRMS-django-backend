from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department, LeaveRequest, PerformanceReview, Attendance

admin.site.register(CustomUser, UserAdmin)
admin.site.register(Department)
admin.site.register(LeaveRequest)
admin.site.register(PerformanceReview)
admin.site.register(Attendance)
