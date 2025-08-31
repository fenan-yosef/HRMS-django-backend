from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.conf import settings
from core.models import AuditLog

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

class AuditLogMiddleware(MiddlewareMixin):
    """Capture API requests and responses for CEO audit logs.

    Keeps payload minimal: method, path, status, user, ua, and simple action code.
    """
    def process_response(self, request, response):
        try:
            # Only log API paths
            path = getattr(request, 'path', '') or ''
            if not path.startswith('/api/'):
                return response
            mode = getattr(settings, 'AUDIT_LOG_MODE', 'minimal')
            if mode == 'off':
                return response
            user = getattr(request, 'user', None)
            actor = user if getattr(user, 'is_authenticated', False) else None
            action = None
            # Heuristic: special-case some paths for nicer summaries
            if path.startswith('/api/users/') and path.endswith('/disable/'):
                action = 'user_disabled'
            elif path.startswith('/api/users/') and path.endswith('/enable/'):
                action = 'user_enabled'
            elif path.startswith('/api/complaints') and request.method == 'POST':
                action = 'complaint_created'
            elif path.startswith('/api/tasks') and request.method == 'POST':
                action = 'task_created'
            # Auth endpoints
            elif path.endswith('/auth/login/'):
                action = 'login_success' if getattr(response, 'status_code', 0) < 400 else 'login_failed'
            elif path.endswith('/auth/token/') and request.method == 'POST':
                action = 'jwt_token_obtained' if getattr(response, 'status_code', 0) < 400 else 'jwt_token_failed'

            # Decide whether to log based on mode
            status_code = getattr(response, 'status_code', 0)
            should_log = False
            if mode == 'minimal':
                # Only auth events and server errors
                should_log = action in {'login_success', 'login_failed', 'jwt_token_obtained', 'jwt_token_failed'} or status_code >= 500
            elif mode == 'important':
                # Auth + key business events + server errors
                important_actions = {
                    'login_success', 'login_failed', 'jwt_token_obtained', 'jwt_token_failed',
                    'user_disabled', 'user_enabled', 'complaint_created', 'task_created'
                }
                should_log = (action in important_actions) or status_code >= 500
            elif mode == 'all':
                # Everything under /api
                should_log = True
                if action is None:
                    action = 'api_call'
            else:
                # Unknown mode -> treat as minimal
                should_log = action in {'login_success', 'login_failed', 'jwt_token_obtained', 'jwt_token_failed'} or status_code >= 500

            if not should_log:
                return response

            AuditLog.objects.create(
                actor=actor,
                action=action or 'api_call',
                summary=f"{request.method} {path} -> {status_code}",
                method=request.method,
                path=path,
                status_code=status_code,
                ip_address=self._get_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                extra={},
            )
        except Exception:
            # Don't break responses if logging fails
            pass
        return response

    def _get_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
