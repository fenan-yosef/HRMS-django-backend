from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager
class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # includes soft-deleted

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)

class CustomUser(AbstractUser, SoftDeleteModel):
    username = None  # Remove username field
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'  # Use email as the unique identifier
    REQUIRED_FIELDS = []  # No additional required fields

    objects = CustomUserManager()
    # Place for any extra fields if needed
    def __str__(self):
        return self.email

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
        ('hr', 'HR'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')

    # Add employee-specific fields from the old Employee table
    job_title = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    # Link to department
    department = models.ForeignKey(
        'department.Department',
        on_delete=models.PROTECT,
        related_name='custom_users',  # renamed to avoid clash with Employee.employees
        null=True,
        blank=True
    )

class Department(SoftDeleteModel):
    name = models.CharField(max_length=100)
    manager = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, related_name='hr_managed_departments')
    code = models.CharField(max_length=50, unique=True, default='DEFAULT_CODE')  # updated max_length
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name

class PerformanceReview(SoftDeleteModel):
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='performance_reviews'
    )
    reviewer = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, related_name='reviews_done')
    score = models.IntegerField()
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Review for {self.employee.first_name} {self.employee.last_name} by {self.reviewer.username if self.reviewer else 'N/A'}"
    class Meta:
        db_table = 'hr_performancereview'

# Add Attendance model back to hr.models
class Attendance(SoftDeleteModel):
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[('Present', 'Present'), ('Absent', 'Absent'), ('Leave', 'Leave')],
        default='Present'
    )
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.first_name} {self.employee.last_name} on {self.date}: {self.status}"

# Password reset OTP model
class PasswordResetOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        # OTP valid for 10 minutes
        return (timezone.now() - self.created_at).total_seconds() > 600

    def __str__(self):
        return f"{self.email} - {self.otp} ({'used' if self.is_used else 'active'})"

