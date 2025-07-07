from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, username, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not username:
            raise ValueError('The given username must be set')
        if email:
            email = self.normalize_email(email)
        
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('CEO', 'CEO'),
        ('Manager', 'Manager'),
        ('HR', 'HR'),
        ('Employee', 'Employee'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Employee')
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
        error_messages={
            'unique': "A user with that username already exists.",
        },
    )
    email = models.EmailField(
        max_length=254,
        blank=True,
    )
    
    objects = CustomUserManager()
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
