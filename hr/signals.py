from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Employee

@receiver(post_save, sender=Employee)
def sync_employee_role(sender, instance, **kwargs):
    if instance.user.role != 'employee':
        instance.user.role = 'employee'
        instance.user.save()
