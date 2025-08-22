from django.conf import settings
from django.db import models
from django.utils import timezone
from core.models import SoftDeleteModel


class Task(SoftDeleteModel):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]
    STATUS_CHOICES = [
        ("todo", "To Do"),
        ("in_progress", "In Progress"),
        ("blocked", "Blocked"),
        ("done", "Done"),
        ("archived", "Archived"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="created_tasks", on_delete=models.SET_NULL, null=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="assigned_tasks_by_me", on_delete=models.SET_NULL, null=True, blank=True)
    assignees = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="assigned_tasks", blank=True)
    department = models.ForeignKey("department.Department", null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo")
    due_date = models.DateTimeField(null=True, blank=True)
    estimate_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["priority"]),
        ]

    def mark_done(self, by_user=None):
        self.status = "done"
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])  # signal will emit history


class TaskAssignment(SoftDeleteModel):
    """Audit record of assignments and reassignments."""
    task = models.ForeignKey(Task, related_name="assignment_history", on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="task_assignments", on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="task_assignments_made", on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class TaskComment(SoftDeleteModel):
    task = models.ForeignKey(Task, related_name="comments", on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class TaskAttachment(SoftDeleteModel):
    task = models.ForeignKey(Task, related_name="attachments", on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to="task_attachments/%Y/%m/%d/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
