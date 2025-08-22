from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, TaskCommentViewSet, TaskAttachmentViewSet, TaskAssignmentViewSet

router = DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"task-comments", TaskCommentViewSet, basename="taskcomment")
router.register(r"task-attachments", TaskAttachmentViewSet, basename="taskattachment")
router.register(r"task-assignments", TaskAssignmentViewSet, basename="taskassignment")

urlpatterns = router.urls
