# hrms_backend/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # The path for the Django admin site you've already been using
    path('admin/', admin.site.urls),
    path('api/', include('hr.urls')),
    path('api/departments/', include('department.urls')),
    # Removed employee.urls as the app is deprecated
    path('api/leaves/', include('leave.urls')),
    path('api/', include('tasks.urls')),
    path('api/settings/', include('core.urls')),


    # This is the new line you are adding.
    # It tells Django that any URL starting with 'api/' should be
    # handled by the urls defined in our 'HR' app.
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
