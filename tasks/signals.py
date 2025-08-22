from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Task, TaskAssignment


def _send_notification_email(subject, message, recipient_list):
    try:
        if not recipient_list:
            return
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, fail_silently=True)
    except Exception:
        # best effort only; logging could be added if project logger configured
        pass


@receiver(post_save, sender=Task)
def notify_task_created(sender, instance: Task, created, **kwargs):
    if created:
        # Notify department manager(s) and creator on new task if department is set
        recipients = []
        if instance.department and instance.department.manager and instance.department.manager.email:
            recipients.append(instance.department.manager.email)
        if instance.creator and instance.creator.email:
            recipients.append(instance.creator.email)
        _send_notification_email(
            subject=f"New Task: {instance.title}",
            message=f"Task '{instance.title}' was created.",
            recipient_list=recipients,
        )


@receiver(post_save, sender=TaskAssignment)
def notify_task_assigned(sender, instance: TaskAssignment, created, **kwargs):
    if created and instance.assigned_to and instance.assigned_to.email:
        _send_notification_email(
            subject=f"Assigned to Task: {instance.task.title}",
            message=f"You have been assigned to task '{instance.task.title}'.",
            recipient_list=[instance.assigned_to.email],
        )
