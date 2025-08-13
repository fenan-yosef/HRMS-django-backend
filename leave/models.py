from django.db import models
from hr.models import CustomUser

from hr.models import SoftDeleteModel

class LeaveRequest(SoftDeleteModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
    ]

    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='leave_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    applied_date = models.DateTimeField(auto_now_add=True)
    deleted_by = models.ForeignKey('hr.CustomUser', null=True, blank=True, on_delete=models.SET_NULL, related_name='deleted_leave_requests')

    class Meta:
        ordering = ['-applied_date']  # Orders by applied_date descending

    def __str__(self):
        return f"{self.employee} - {self.start_date} to {self.end_date} ({self.status})"

        def soft_delete(self, user=None):
            from django.utils import timezone
            self.deleted_at = timezone.now()
            self.deleted_by = user
            self.save(update_fields=['deleted_at', 'deleted_by'])

    def get_approvers(self):
        """
        Returns queryset of users who can approve this leave request based on employee role.
        """
        from hr.models import CustomUser
        role = (self.employee.role or '').lower()
        if role == 'employee':
            # Manager of department, any CEO, any HR
            approvers = CustomUser.objects.filter(
                models.Q(role__iexact='ceo') |
                models.Q(role__iexact='hr') |
                (models.Q(role__iexact='manager') & models.Q(department=self.employee.department))
            )
        elif role == 'manager':
            # Any CEO or any HR
            approvers = CustomUser.objects.filter(
                models.Q(role__iexact='ceo') |
                models.Q(role__iexact='hr')
            )
        elif role == 'hr':
            # Any CEO
            approvers = CustomUser.objects.filter(role__iexact='ceo')
        elif role == 'ceo':
            # Any HR
            approvers = CustomUser.objects.filter(role__iexact='hr')
        else:
            approvers = CustomUser.objects.none()
        return approvers
