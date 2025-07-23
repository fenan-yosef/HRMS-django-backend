from django.db import models
from department.models import Department
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
import random
import string
import logging

logger = logging.getLogger(__name__)

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

    class Meta:
        ordering = ['last_name', 'first_name']  # Default ordering by last name, then first name

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.pk:  # If it's a new employee
            if not self.password:
                self.password = make_password(Employee.DEFAULT_PASSWORD)  # Hash the default password
        super().save(*args, **kwargs)


@receiver(post_save, sender=Employee)
def send_initial_credentials(sender, instance, created, **kwargs):
    if created:
        try:
            from hr.models import CustomUser
            # Generate a random password
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            
            # Update the associated CustomUser
            user = CustomUser.objects.create_user(
                email=instance.email,
                password=password,
                role='Employee'
            )

            # Send email with credentials
            subject = "Welcome to Guest Home PLC!"
            message = f"Hello {instance.first_name},\n\nYour account has been created. Here are your login credentials:\n\nEmail: {instance.email}\nPassword: {password}\n\nPlease log in and change your password immediately.\n\nBest regards,\nHR Team"
            
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [instance.email],
                fail_silently=False,
            )
            logger.info(f"Password sent successfully to {instance.email}")

        except Exception as e:
            logger.error(f"Error sending password to {instance.email}: {e}", exc_info=True)
