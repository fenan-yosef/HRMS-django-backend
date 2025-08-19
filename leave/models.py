from django.db import models
from django.conf import settings
from core.models import SoftDeleteModel
from django.utils import timezone

class LeaveRequestQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(status=LeaveRequest.Status.APPROVED)

    def pending(self):
        return self.filter(status=LeaveRequest.Status.PENDING)

    def for_user(self, user):
        return self.filter(employee=user)


class LeaveRequest(SoftDeleteModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        DENIED = 'DENIED', 'Denied'

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_requests'
    )
    leave_type = models.ForeignKey(
        'LeaveType', on_delete=models.PROTECT, related_name='leave_requests', null=True, blank=True
    )
    start_date = models.DateField()
    end_date = models.DateField()
    duration_days = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    applied_date = models.DateTimeField(auto_now_add=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='requested_leave_requests'
    )

    objects = LeaveRequestQuerySet.as_manager()

    class Meta:
        ordering = ['-applied_date']
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gte=models.F('start_date')),
                name='leave_end_after_start'
            )
        ]

    def __str__(self):
        return f"{self.employee} - {self.start_date} to {self.end_date} ({self.status})"

    def soft_delete(self, user=None):
        """Soft-delete the leave request by setting deleted_at timestamp."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def get_approvers(self):
        """Return queryset of users who can approve this leave request based on employee role."""
        from django.contrib.auth import get_user_model

        CustomUser = get_user_model()
        role = str(getattr(self.employee, 'role', '') or '').lower()

        if role == 'employee':
            approvers = CustomUser.objects.filter(
                models.Q(role__iexact='ceo') |
                models.Q(role__iexact='hr') |
                (models.Q(role__iexact='manager') & models.Q(department=self.employee.department))
            )
        elif role == 'manager':
            approvers = CustomUser.objects.filter(
                models.Q(role__iexact='ceo') |
                models.Q(role__iexact='hr')
            )
        elif role == 'hr':
            approvers = CustomUser.objects.filter(role__iexact='ceo')
        elif role == 'ceo':
            approvers = CustomUser.objects.filter(role__iexact='hr')
        else:
            approvers = CustomUser.objects.none()

        return approvers


class LeaveType(SoftDeleteModel):
    """Normalized leave types (annual, sick, unpaid) with policies.

    Policies here are intentionally light — business rules should
    live in services or managers rather than in model constraints.
    """

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    default_allowance_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    requires_approval = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class LeaveBalance(models.Model):
    """Tracks remaining allowance per user and leave type for a year/period.

    This is separate from requests to allow fast checks and historical tracking.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='balances')
    year = models.IntegerField()
    allowance = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    used = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        unique_together = [('user', 'leave_type', 'year')]

    @property
    def remaining(self):
        return max(self.allowance - self.used, 0)


class LeaveApproval(models.Model):
    """Approval record for a LeaveRequest. Multiple approvers allowed.

    Keeping approvals separate normalizes the many-to-one approval flow and
    keeps auditing easier.
    """

    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='approvals_done')
    approved_at = models.DateTimeField(auto_now_add=True)
    decision = models.CharField(max_length=10, choices=LeaveRequest.Status.choices)
    comment = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=['approver']), models.Index(fields=['leave_request'])]

    def __str__(self):
        return f"{self.leave_request} - {self.approver}: {self.decision}"
