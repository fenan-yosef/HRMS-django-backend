# filepath: department/models.py
from django.db import models
from django.conf import settings

class Department(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    code        = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    manager     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='department_managed_departments')

    def __str__(self):
        return self.name