from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from .models import SystemSetting
from .serializers import SystemSettingSerializer, ALLOWED_SETTINGS
from hr.permissions import AnyOf, IsCEO, IsHR


class SystemSettingViewSet(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin,
                           mixins.CreateModelMixin,
                           mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    # Keep class-level permission simple and instantiate AnyOf at runtime
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # Instantiate default permission classes and our AnyOf composite permission
        perms = [p() for p in self.permission_classes]
        # AnyOf expects permission classes as args and returns a permission instance
        perms.append(AnyOf(IsCEO, IsHR))
        return perms

    def get_queryset(self):
        qs = super().get_queryset()
        # Limit to allowed settings keys to avoid exposing unrelated records
        return qs.filter(key__in=list(ALLOWED_SETTINGS.keys()))
