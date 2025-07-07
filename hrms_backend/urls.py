# hrms_backend/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # The path for the Django admin site you've already been using
    path('admin/', admin.site.urls),
    path('api/', include('hr.urls')),
    path('api/departments/', include('department.urls')),
    path('api/employees/', include('employee.urls')),


    # This is the new line you are adding.
    # It tells Django that any URL starting with 'api/' should be
    # handled by the urls defined in our 'HR' app.
]
