from django.contrib import admin
from .models import Task, TaskComment, TaskAttachment, TaskAssignment


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "priority", "status", "department", "due_date", "created_at")
    list_filter = ("priority", "status", "department")
    search_fields = ("title", "description")


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "author", "created_at")


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "uploaded_by", "uploaded_at")


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "assigned_to", "assigned_by", "created_at")
