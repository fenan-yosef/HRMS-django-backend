from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Task, TaskComment, TaskAttachment, TaskAssignment


class UserPKField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        super().__init__(queryset=get_user_model().objects.all(), **kwargs)


class TaskSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source="creator.id")
    assigned_by = serializers.ReadOnlyField(source="assigned_by.id")
    assignees = UserPKField(many=True, required=False)

    class Meta:
        model = Task
        fields = "__all__"


class TaskCommentSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source="author.id")

    class Meta:
        model = TaskComment
        fields = ["id", "task", "author", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class TaskAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.ReadOnlyField(source="uploaded_by.id")

    class Meta:
        model = TaskAttachment
        fields = ["id", "task", "uploaded_by", "file", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]


class TaskAssignmentSerializer(serializers.ModelSerializer):
    assigned_by = serializers.ReadOnlyField(source="assigned_by.id")

    class Meta:
        model = TaskAssignment
        fields = ["id", "task", "assigned_to", "assigned_by", "created_at"]
        read_only_fields = ["id", "created_at"]
