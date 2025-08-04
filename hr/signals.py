from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser

@receiver(post_save, sender=CustomUser)
def sync_employee_role(sender, instance, **kwargs):
    if instance.role == 'employee':
        # Perform any additional logic for employees if needed
        pass
