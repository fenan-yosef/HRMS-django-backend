from typing import Optional, Dict, Any
from django.http import HttpRequest
from django.utils import timezone
from .models import AuditLog


def log_audit(request: Optional[HttpRequest] = None,
              *,
              actor=None,
              action: str,
              summary: str,
              target_model: str = "",
              target_object_id: str = "",
              extra: Optional[Dict[str, Any]] = None):
    """Create an AuditLog record with safe defaults.

    Either pass `request` (preferred) or explicit `actor`.
    """
    try:
        if request is not None:
            actor_obj = getattr(request, 'user', None)
            if not getattr(actor_obj, 'is_authenticated', False):
                actor_obj = None
            method = getattr(request, 'method', '')
            path = getattr(request, 'path', '')
            ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')
            ua = request.META.get('HTTP_USER_AGENT', '')[:500]
        else:
            actor_obj = actor
            method = ''
            path = ''
            ip = ''
            ua = ''
        AuditLog.objects.create(
            actor=actor_obj,
            action=action,
            summary=summary,
            method=method,
            path=path,
            status_code=None,
            ip_address=ip,
            user_agent=ua,
            target_model=target_model or '',
            target_object_id=str(target_object_id or ''),
            extra=extra or {},
        )
    except Exception:
        # Never break business flows for audit failures
        pass
