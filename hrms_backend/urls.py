# hrms_backend/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # The path for the Django admin site you've already been using
    path('admin/', admin.site.urls),

    # This is the new line you are adding.
    # It tells Django that any URL starting with 'api/' should be
    # handled by the urls defined in our 'hr_system' app.
    path('api/', include('hr_system.urls')),
]
