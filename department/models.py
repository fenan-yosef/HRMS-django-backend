# filepath: department/models.py
from django.db import models
from core.models import SoftDeleteModel
from django.conf import settings

class Department(SoftDeleteModel):
    name        = models.CharField(max_length=100)
    code        = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    manager     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='managed_departments', null=True, blank=True)

    def __str__(self):
        return self.name