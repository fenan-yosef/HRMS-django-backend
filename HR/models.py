# hr_system/models.py

from django.db import models
from django.conf import settings # Recommended for ForeignKey to User model
from django.contrib.auth.models import User



# It's a good practice to link your Employee model to Django's built-in User model.
# This handles authentication (login, password) securely.
# Here, we assume a One-to-One relationship: one User has one Employee profile.
# If an employee should not be a user that can log in, you can remove the user ForeignKey.
# For now, we'll make it optional (blank=True, null=True).



class HR(models.Model):
    """
    Represents core HR data for an employee.
    """
    User = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        blank=True,  # Optional, if you want to allow employees without a user account
        null=True
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    date_joined = models.DateField(auto_now_add=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_manager = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    # Add any additional fields that are relevant to your HR system 
    # such as performance reviews, training records, etc.
    


    def __str__(self):
        return self.user.username  # Or any other suitable

