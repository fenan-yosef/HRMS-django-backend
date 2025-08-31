from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import SystemSetting, AuditLog
from .serializers import SystemSettingSerializer, ALLOWED_SETTINGS, AuditLogSerializer
from hr.permissions import AnyOf, IsCEO, IsHR
import logging
from rest_framework.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated as DRFIsAuthenticated
from rest_framework import viewsets, pagination

logger = logging.getLogger(__name__)


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
        """Instantiate default permission classes and our AnyOf composite permission.

        Keep the class-level permission simple (IsAuthenticated) and append a
        composite permission that allows either CEO or HR.
        """
        perms = [perm() for perm in self.permission_classes]
        # AnyOf expects permission classes; append the composite permission instance
        perms.append(AnyOf(IsCEO, IsHR))
        return perms

    def get_queryset(self):
        qs = super().get_queryset()
        # Limit to allowed settings keys to avoid exposing unrelated records
        return qs.filter(key__in=list(ALLOWED_SETTINGS.keys()))

    def create(self, request, *args, **kwargs):
        """Create with clearer error handling so we don't return HTML 500 pages.

        Validates, attempts to save, and translates IntegrityError into a 400.
        """
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        except ValidationError as ve:
            # If the validation error is the unique key constraint, return the existing record
            key = request.data.get('key')
            if key and SystemSetting.objects.filter(key=key).exists():
                existing = SystemSetting.objects.get(key=key)
                existing_data = SystemSettingSerializer(existing).data
                return Response({'detail': 'setting with this key already exists', 'setting': existing_data}, status=400)
            return Response({'errors': ve.detail}, status=400)
        except IntegrityError as ie:
            logger.exception("IntegrityError creating SystemSetting")
            return Response({'detail': 'Database error, possibly duplicate key.'}, status=400)
        except Exception as exc:
            logger.exception("Unhandled error creating SystemSetting")
            return Response({'detail': 'Internal server error', 'error': str(exc)}, status=500)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    # Removed by-key @action routes to avoid conflicts with the dedicated APIView


class SystemSettingByKeyView(APIView):
    """Dedicated view for GET/POST/PATCH by key at /api/settings/system/by-key/<key>/"""
    permission_classes = [DRFIsAuthenticated]

    def _is_ceo_or_hr(self, user):
        return getattr(user, 'role', '').lower() in ('ceo', 'hr') or user.is_superuser

    def get(self, request, key):
        logger.info('SystemSettingByKeyView GET request key=%s user=%s', key, getattr(request.user, 'email', None))
        if key not in ALLOWED_SETTINGS:
            return Response({'detail': 'Setting key not allowed.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            s = SystemSetting.objects.get(key=key)
        except SystemSetting.DoesNotExist:
            logger.info('SystemSetting not found for key=%s', key)
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        logger.info('SystemSettingByKeyView GET success key=%s', key)
        return Response(SystemSettingSerializer(s).data)

    def post(self, request, key):
        logger.info('SystemSettingByKeyView POST attempt key=%s user=%s', key, getattr(request.user, 'email', None))
        if not self._is_ceo_or_hr(request.user):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        if key not in ALLOWED_SETTINGS:
            return Response({'detail': 'Setting key not allowed.'}, status=status.HTTP_400_BAD_REQUEST)
        if SystemSetting.objects.filter(key=key).exists():
            existing = SystemSetting.objects.get(key=key)
            return Response({'detail': 'setting with this key already exists', 'setting': SystemSettingSerializer(existing).data}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data['key'] = key
        serializer = SystemSettingSerializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ValidationError as ve:
            return Response({'errors': ve.detail}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response({'detail': 'Database error, possibly duplicate key.'}, status=status.HTTP_400_BAD_REQUEST)

        logger.info('SystemSettingByKeyView POST created key=%s id=%s', key, serializer.data.get('id'))
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request, key):
        logger.info('SystemSettingByKeyView PATCH attempt key=%s user=%s', key, getattr(request.user, 'email', None))
        if not self._is_ceo_or_hr(request.user):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        if key not in ALLOWED_SETTINGS:
            return Response({'detail': 'Setting key not allowed.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            obj = SystemSetting.objects.get(key=key)
        except SystemSetting.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        data = request.data.copy()
        data.pop('key', None)
        serializer = SystemSettingSerializer(obj, data=data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ValidationError as ve:
            return Response({'errors': ve.detail}, status=status.HTTP_400_BAD_REQUEST)

        logger.info('SystemSettingByKeyView PATCH success key=%s', key)
        return Response(serializer.data)


class FifteenPerPagePagination(pagination.PageNumberPagination):
    page_size = 15
    max_page_size = 50


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [DRFIsAuthenticated]
    pagination_class = FifteenPerPagePagination

    def get_permissions(self):
        # Instantiate the base DRF permission and our composite AnyOf(IsCEO)
        return [DRFIsAuthenticated(), AnyOf(IsCEO)]

    def get_queryset(self):
        qs = super().get_queryset()
        # Optional filters: action, actor email contains, path contains
        action = self.request.query_params.get('action')
        actor = self.request.query_params.get('actor')
        path = self.request.query_params.get('path')
        if action:
            qs = qs.filter(action__iexact=action)
        if actor:
            qs = qs.filter(actor__email__icontains=actor)
        if path:
            qs = qs.filter(path__icontains=path)
        return qs
