from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import LeaveRequest
from .serializers import LeaveRequestSerializer
import logging
from rest_framework.response import Response

logger = logging.getLogger(__name__)

class LeaveRequestViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing leave request instances.
    """
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.exception("Error creating leave request")
            return Response({"error": "An error occurred while creating the leave request."}, status=500)

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            logger.exception("Error updating leave request")
            return Response({"error": "An error occurred while updating the leave request."}, status=500)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.exception("Error deleting leave request")
            return Response({"error": "An error occurred while deleting the leave request."}, status=500)

    def perform_create(self, serializer):
        user = self.request.user
        # If HR, allow specifying employee; else, force employee to self
        if hasattr(user, 'role') and user.role == 'HR':
            employee_id = self.request.data.get('employee')
            if not employee_id:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'employee': 'This field is required for HR.'})
            serializer.save(employee_id=employee_id)
        else:
            serializer.save(employee=user)
    # Optionally, add logging to other methods as well (e.g., list, retrieve)
