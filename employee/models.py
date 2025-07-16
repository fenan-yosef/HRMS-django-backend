from django.db import models
from department.models import Department
from django.conf import settings
from django.contrib.auth.hashers import make_password

class Employee(models.Model):
    first_name    = models.CharField(max_length=50)
    last_name     = models.CharField(max_length=50)
    email         = models.EmailField(unique=True)
    job_title     = models.CharField(max_length=100)
    phone_number  = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    date_joined   = models.DateField(auto_now_add=True)
    is_active     = models.BooleanField(default=True)
    password       = models.CharField(max_length=128)  # Store hashed password
    department    = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='employees')

    DEFAULT_PASSWORD = 'default_password'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.pk:  # If it's a new employee
            if not self.password:
                self.password = make_password(Employee.DEFAULT_PASSWORD)  # Hash the default password
        super().save(*args, **kwargs)