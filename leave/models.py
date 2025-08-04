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

    class Meta:
        ordering = ['-applied_date']  # Orders by applied_date descending

    def __str__(self):
        return f"{self.employee} - {self.start_date} to {self.end_date} ({self.status})"
