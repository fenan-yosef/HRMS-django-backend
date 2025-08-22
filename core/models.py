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
