from rest_framework import serializers
from .models import SystemSetting, AuditLog


ALLOWED_SETTINGS = {
    # key: expected type ('int' or 'decimal' or 'text')
    'annual_leave_request_max_days': 'int',
}


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = ['key', 'int_value', 'decimal_value', 'text_value', 'description', 'updated_at']
        read_only_fields = ['updated_at']

    def validate(self, attrs):
        key = attrs.get('key') or getattr(self.instance, 'key', None)
        if key in ALLOWED_SETTINGS:
            expected = ALLOWED_SETTINGS[key]
            if expected == 'int':
                val = attrs.get('int_value', getattr(self.instance, 'int_value', None))
                if val is None:
                    raise serializers.ValidationError({'int_value': 'This field is required for this setting.'})
                if val < 0:
                    raise serializers.ValidationError({'int_value': 'Value must be >= 0.'})
            elif expected == 'decimal':
                val = attrs.get('decimal_value', getattr(self.instance, 'decimal_value', None))
                if val is None:
                    raise serializers.ValidationError({'decimal_value': 'This field is required for this setting.'})
        return attrs


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'timestamp', 'actor_email', 'action', 'summary', 'method', 'path', 'status_code',
            'ip_address', 'user_agent', 'target_model', 'target_object_id', 'extra'
        ]

    def get_actor_email(self, obj):
        return getattr(obj.actor, 'email', None)
