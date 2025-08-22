from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from core.models import SoftDeleteModel


## SoftDeleteModel now lives in core.models


class CustomUserManager(BaseUserManager):
    """Model manager for CustomUser using email as identifier."""

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email field must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser, SoftDeleteModel):
    username = None
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MANAGER = "manager", "Manager"
        EMPLOYEE = "employee", "Employee"
        HR = "hr", "HR"
        CEO = "ceo", "CEO"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)

    job_title = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)

    department = models.ForeignKey(
        "department.Department",
        on_delete=models.PROTECT,
        related_name="custom_users",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.email
    
    class Meta:
        ordering = ['email']


# ----- Performance Management models (review cycles, competency, reviews, scores) -----


class ReviewCycle(SoftDeleteModel):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"


class RatingScale(models.Model):
    name = models.CharField(max_length=100)
    min_value = models.IntegerField(default=1)
    max_value = models.IntegerField(default=5)
    labels = models.JSONField(default=dict, blank=True)  # {"1": "Poor", "5": "Excellent"}

    def __str__(self):
        return self.name


class Competency(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    rating_scale = models.ForeignKey(RatingScale, on_delete=models.PROTECT, related_name="competencies", null=True, blank=True)

    def __str__(self):
        return self.name


class PerformanceReview(SoftDeleteModel):
    REVIEW_TYPE_CHOICES = [("annual", "Annual"), ("mid", "Mid-year"), ("probation", "Probation")]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("manager_review", "Manager Review"),
        ("calibration", "Calibration"),
        ("finalized", "Finalized"),
        ("archived", "Archived"),
    ]

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="performance_reviews")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="reviews_done")
    review_cycle = models.ForeignKey(ReviewCycle, on_delete=models.PROTECT, related_name="reviews", null=True, blank=True)
    review_type = models.CharField(max_length=32, choices=REVIEW_TYPE_CHOICES, default="annual")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="draft")
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    comments = models.TextField(blank=True)
    self_assessment = models.TextField(blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "hr_performancereview"
        indexes = [models.Index(fields=["employee"]), models.Index(fields=["review_cycle"]) ]
        unique_together = [("employee", "review_cycle", "review_type")]

    def __str__(self):
        return f"Review {self.pk} for {self.employee} ({self.review_cycle})"

    def finalize(self, by_user=None):
        self.status = "finalized"
        self.finalized_at = timezone.now()
        self.save(update_fields=["status", "finalized_at"])
        # create snapshot
        ReviewSnapshot.create_from_review(self, created_by=by_user)


class ReviewScore(models.Model):
    review = models.ForeignKey(PerformanceReview, on_delete=models.CASCADE, related_name="scores")
    competency = models.ForeignKey(Competency, on_delete=models.PROTECT)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    comment = models.TextField(blank=True)

    class Meta:
        unique_together = [("review", "competency")]

    def __str__(self):
        return f"{self.review} - {self.competency}: {self.score}"


class ReviewSnapshot(models.Model):
    review = models.OneToOneField(PerformanceReview, on_delete=models.CASCADE, related_name="snapshot")
    snapshot = models.JSONField()  # immutable JSON snapshot of review + scores
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    @classmethod
    def create_from_review(cls, review: PerformanceReview, created_by=None):
        data = {
            "employee": review.employee_id,
            "reviewer": review.reviewer_id,
            "review_cycle": review.review_cycle_id,
            "review_type": review.review_type,
            "status": review.status,
            "overall_score": float(review.overall_score) if review.overall_score is not None else None,
            "comments": review.comments,
            "self_assessment": review.self_assessment,
            "scores": [
                {"competency": s.competency.name, "score": float(s.score), "comment": s.comment} for s in review.scores.all()
            ],
            "finalized_at": review.finalized_at.isoformat() if review.finalized_at else None,
        }
        return cls.objects.create(review=review, snapshot=data, created_by=created_by)


# ----- Goal / OKR models -----


class Goal(SoftDeleteModel):
    STATUS_CHOICES = [("open", "Open"), ("at_risk", "At Risk"), ("closed", "Closed"), ("cancelled", "Cancelled")]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_goals")
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_goals")
    department = models.ForeignKey("department.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="goals")
    start_date = models.DateField(null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="open")
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    visibility = models.CharField(max_length=32, default="team")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.owner})"


class GoalKeyResult(models.Model):
    METRIC_TYPE = [("numeric", "Numeric"), ("percent", "Percent"), ("binary", "Binary")]

    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="key_results")
    description = models.TextField()
    metric_type = models.CharField(max_length=32, choices=METRIC_TYPE, default="numeric")
    baseline = models.FloatField(null=True, blank=True)
    target = models.FloatField(null=True, blank=True)
    current_value = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=50, blank=True)

    def progress(self):
        if self.target is None or self.baseline is None:
            return None
        try:
            return (self.current_value - self.baseline) / (self.target - self.baseline)
        except Exception:
            return None

    def __str__(self):
        return f"KR for {self.goal}: {self.description[:40]}"


class GoalProgressUpdate(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="progress_updates")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    value = models.FloatField(null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Progress on {self.goal} by {self.updated_by} @ {self.created_at}"


class GoalParticipant(models.Model):
    ROLE_CHOICES = [("owner", "Owner"), ("contributor", "Contributor"), ("watcher", "Watcher")]
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default="contributor")

    class Meta:
        unique_together = [("goal", "user")]

    def __str__(self):
        return f"{self.user} as {self.role} on {self.goal}"


class GoalSnapshot(models.Model):
    goal = models.OneToOneField(Goal, on_delete=models.CASCADE, related_name="snapshot")
    snapshot = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Snapshot for {self.goal} @ {self.created_at}"


# ----- Attendance and OTP kept for backwards compatibility -----


class Attendance(SoftDeleteModel):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendances")
    date = models.DateField()
    status = models.CharField(max_length=20, choices=[("Present", "Present"), ("Absent", "Absent"), ("Leave", "Leave")], default="Present")
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    work_duration = models.DurationField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} on {self.date}: {self.status}"

    def finalize_duration(self):
        if self.check_in_time and self.check_out_time:
            if not self.work_duration:
                dt_in = timezone.datetime.combine(self.date, self.check_in_time, tzinfo=timezone.get_current_timezone())
                dt_out = timezone.datetime.combine(self.date, self.check_out_time, tzinfo=timezone.get_current_timezone())
                if dt_out < dt_in:
                    dt_out = dt_out + timezone.timedelta(days=1)
                self.work_duration = dt_out - dt_in
                self.save(update_fields=["work_duration"])

    class Meta:
        constraints = [models.UniqueConstraint(fields=["employee", "date"], name="uniq_attendance_employee_date")]


class PasswordResetOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return (timezone.now() - self.created_at).total_seconds() > 600

    def __str__(self):
        return f"{self.email} - {self.otp} ({'used' if self.is_used else 'active'})"

