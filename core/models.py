from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def with_deleted(self):
        return self.model.all_objects.all()

    def only_deleted(self):
        return self.model.all_objects.filter(deleted_at__isnull=False)

    def restore(self):
        return self.update(deleted_at=None)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True)


class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])


class SystemSetting(models.Model):
    """Simple key/value table for small site-wide settings editable by CEO/HR.

    We keep a couple of typed value fields to make reads simple. Add new keys
    as needed. For the annual leave request limit we use the key
    'annual_leave_request_max_days'.
    """

    key = models.CharField(max_length=100, unique=True)
    int_value = models.IntegerField(null=True, blank=True)
    decimal_value = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    text_value = models.TextField(blank=True)
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key}"

    class Meta:
        ordering = ['key']

    @classmethod
    def get_int(cls, key, default=None):
        try:
            s = cls.objects.get(key=key)
            if s.int_value is not None:
                return s.int_value
            if s.decimal_value is not None:
                return int(s.decimal_value)
        except cls.DoesNotExist:
            return default


class AuditLog(models.Model):
    """Lightweight audit log for API actions.

    Captures who did what, when, and basic HTTP context so CEO can review.
    """

    timestamp = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey('hr.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=100, blank=True)  # short code e.g., 'api_call', 'user_disabled', 'complaint_created'
    summary = models.TextField(blank=True)  # human-friendly description
    method = models.CharField(max_length=10, blank=True)
    path = models.CharField(max_length=500, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    ip_address = models.CharField(max_length=100, blank=True)
    user_agent = models.TextField(blank=True)
    target_model = models.CharField(max_length=200, blank=True)
    target_object_id = models.CharField(max_length=100, blank=True)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        who = getattr(self.actor, 'email', 'system') if self.actor else 'anonymous'
        return f"[{self.timestamp:%Y-%m-%d %H:%M:%S}] {who} {self.action}: {self.summary[:60]}"

    @classmethod
    def get_decimal(cls, key, default=None):
        try:
            s = cls.objects.get(key=key)
            if s.decimal_value is not None:
                return s.decimal_value
            if s.int_value is not None:
                return s.int_value
        except cls.DoesNotExist:
            return default
