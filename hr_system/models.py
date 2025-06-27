# hr_system/models.py

from django.db import models
from django.conf import settings # Recommended for ForeignKey to User model

# It's a good practice to link your Employee model to Django's built-in User model.
# This handles authentication (login, password) securely.
# Here, we assume a One-to-One relationship: one User has one Employee profile.
# If an employee should not be a user that can log in, you can remove the user ForeignKey.
# For now, we'll make it optional (blank=True, null=True).

class Department(models.Model):
    """
    Represents a department within the company.
    Corresponds to the Department Table in the documentation.
    """
    name = models.CharField(max_length=100, unique=True, help_text="Name of the department")
    location = models.CharField(max_length=100, blank=True, null=True, help_text="Physical location of the department")

    def __str__(self):
        return self.name

class Employee(models.Model):
    """
    Represents an employee in the company.
    Corresponds to the Employee Table in the documentation.
    """
    class Gender(models.TextChoices):
        MALE = 'Male', 'Male'
        FEMALE = 'Female', 'Female'
        OTHER = 'Other', 'Other'

    class Status(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'
        ON_LEAVE = 'On Leave', 'On Leave'

    # Link to the built-in Django User model for authentication
    # This is highly recommended for managing logins and permissions.
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    
    # Personal Information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=Gender.choices)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    # Employment Information
    hire_date = models.DateField()
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    job_title = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2, help_text="Employee's current salary")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Payroll(models.Model):
    """
    Represents a payroll record for an employee.
    Corresponds to the Payroll Table in the documentation.
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')
    pay_period_start = models.DateField()
    pay_period_end = models.DateField()
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()

    def __str__(self):
        return f"Payroll for {self.employee} ({self.pay_period_start} to {self.pay_period_end})"
        
    def save(self, *args, **kwargs):
        # Automatically calculate net salary before saving
        self.net_salary = self.gross_salary - self.deductions
        super().save(*args, **kwargs)

class Leave(models.Model):
    """
    Represents a leave request from an employee.
    Corresponds to the Leave Table in the documentation.
    """
    class LeaveType(models.TextChoices):
        SICK = 'Sick', 'Sick'
        VACATION = 'Vacation', 'Vacation'
        MATERNITY = 'Maternity', 'Maternity'
        PATERNITY = 'Paternity', 'Paternity'
        UNPAID = 'Unpaid', 'Unpaid'

    class LeaveStatus(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        APPROVED = 'Approved', 'Approved'
        REJECTED = 'Rejected', 'Rejected'

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LeaveType.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=LeaveStatus.choices, default=LeaveStatus.PENDING)
    reason = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')

    def __str__(self):
        return f"{self.leave_type} request for {self.employee}"

class PerformanceReview(models.Model):
    """
    Represents a performance review for an employee.
    Corresponds to the PerformanceReview Table in the documentation.
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='reviews_received')
    reviewer = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='reviews_given')
    review_date = models.DateField()
    rating = models.IntegerField(help_text="Performance rating (1-5)", choices=[(i, i) for i in range(1, 6)])
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Review for {self.employee} on {self.review_date}"

