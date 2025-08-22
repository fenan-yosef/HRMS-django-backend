from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Task, TaskComment, TaskAttachment, TaskAssignment
from .serializers import (
    TaskSerializer,
    TaskCommentSerializer,
    TaskAttachmentSerializer,
    TaskAssignmentSerializer,
)
from .permissions import CanManageTasks


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related("creator", "department").prefetch_related("assignees")
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageTasks]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["due_date", "priority", "created_at"]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        # Scope: HR/CEO see all; managers see dept; employees see assigned/created
        if user.is_superuser or getattr(user, "role", "").lower() in {"hr", "ceo"}:
            return qs
        if getattr(user, "role", "").lower() == "manager":
            return qs.filter(Q(department_id=user.department_id) | Q(creator_id=user.id) | Q(assignees=user))
        return qs.filter(Q(creator_id=user.id) | Q(assignees=user))

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user, assigned_by=self.request.user)

    @action(detail=True, methods=["post"])  # POST /tasks/{id}/assign/
    def assign(self, request, pk=None):
        task = self.get_object()
        user_ids = request.data.get("assignees", []) or []
        if not isinstance(user_ids, list):
            return Response({"detail": "assignees must be a list of user ids"}, status=400)
        with transaction.atomic():
            task.assignees.add(*user_ids)
            for uid in user_ids:
                TaskAssignment.objects.create(task=task, assigned_to_id=uid, assigned_by=request.user)
        return Response({"status": "assigned", "assignees": list(task.assignees.values_list("id", flat=True))})

    @action(detail=True, methods=["post"])  # POST /tasks/{id}/unassign/
    def unassign(self, request, pk=None):
        task = self.get_object()
        user_ids = request.data.get("assignees", []) or []
        if not isinstance(user_ids, list):
            return Response({"detail": "assignees must be a list of user ids"}, status=400)
        task.assignees.remove(*user_ids)
        return Response({"status": "unassigned", "assignees": list(task.assignees.values_list("id", flat=True))})

    @action(detail=True, methods=["post"])  # POST /tasks/{id}/mark_done/
    def mark_done(self, request, pk=None):
        task = self.get_object()
        task.mark_done(by_user=request.user)
        return Response({"status": "done", "completed_at": task.completed_at})


class TaskCommentViewSet(viewsets.ModelViewSet):
    queryset = TaskComment.objects.select_related("task", "author")
    serializer_class = TaskCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        # only comments on visible tasks to user
        return qs.filter(task__in=TaskViewSet().get_queryset())


class TaskAttachmentViewSet(viewsets.ModelViewSet):
    queryset = TaskAttachment.objects.select_related("task", "uploaded_by")
    serializer_class = TaskAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        return qs.filter(task__in=TaskViewSet().get_queryset())


class TaskAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TaskAssignment.objects.select_related("task", "assigned_by", "assigned_to")
    serializer_class = TaskAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if getattr(user, "role", "").lower() in {"hr", "ceo"} or user.is_superuser:
            return qs
        if getattr(user, "role", "").lower() == "manager":
            return qs.filter(task__department_id=user.department_id)
        return qs.filter(Q(assigned_to=user) | Q(assigned_by=user))
