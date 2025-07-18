from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department, PerformanceReview, Attendance

admin.site.register(CustomUser, UserAdmin)
admin.site.register(Department)
admin.site.register(PerformanceReview)
admin.site.register(Attendance)
