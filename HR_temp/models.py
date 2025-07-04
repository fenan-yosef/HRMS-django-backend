from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('CEO', 'CEO'),
        ('Manager', 'Manager'),
        ('HR', 'HR'),
        ('Employee', 'Employee'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Employee')
    # Place for any extra fields if needed
    def __str__(self):
        return self.username

class Department(models.Model):
    name = models.CharField(max_length=100)
    manager = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, related_name='managed_departments')
    def __str__(self):
        return self.name

class LeaveRequest(models.Model):
    employee = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='leave_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.employee.username}: {self.start_date} to {self.end_date} ({self.status})"

class PerformanceReview(models.Model):
    employee = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='performance_reviews')
    reviewer = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, related_name='reviews_done')
    score = models.IntegerField()
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Review for {self.employee.username} by {self.reviewer.username if self.reviewer else 'N/A'}"
    class Meta:
        db_table = 'hr_performancereview'

class Attendance(models.Model):
    employee = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=[('Present', 'Present'), ('Absent', 'Absent'), ('Leave', 'Leave')], default='Present')
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.employee.username} on {self.date}: {self.status}"
