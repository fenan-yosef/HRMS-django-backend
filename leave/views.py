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
    def get_queryset(self):
        user = self.request.user
        role = str(getattr(user, 'role', '') or '')
        role_lower = role.lower()
        # Employees only see their own leave requests
        if role_lower == 'employee':
            return LeaveRequest.objects.filter(employee=user)
        # HR and CEO see all, including soft-deleted
        if role_lower in ['hr', 'ceo']:
            return LeaveRequest.all_objects.all()
        # Others see only active
        return LeaveRequest.objects.all()
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
            instance = self.get_object()
            instance.soft_delete(user=request.user)
            serializer = self.get_serializer(instance)
            return Response({"message": "Leave request soft deleted.", "leave_request": serializer.data})
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
            # Before saving, enforce the CEO-configured yearly cap for total requested days
            from core.models import SystemSetting
            max_days = SystemSetting.get_int('annual_leave_request_max_days', default=15)

            start_date = serializer.validated_data.get('start_date')
            end_date = serializer.validated_data.get('end_date')
            if start_date and end_date:
                requested_days = (end_date - start_date).days + 1
            else:
                requested_days = 0

            # Calculate already granted approved days for current year
            from django.utils import timezone
            year = timezone.now().year
            already_approved = LeaveRequest.objects.approved().filter(employee=user, start_date__year=year)
            approved_total = 0
            for r in already_approved:
                if r.duration_days is not None:
                    approved_total += float(r.duration_days)
                else:
                    approved_total += (r.end_date - r.start_date).days + 1

            if approved_total + requested_days > max_days:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'non_field_errors': [
                        f'Request exceeds annual allowed leave request limit of {max_days} days. You have {max_days - approved_total} days remaining.'
                    ]
                })

            serializer.save(employee=user)
    # Optionally, add logging to other methods as well (e.g., list, retrieve)
 