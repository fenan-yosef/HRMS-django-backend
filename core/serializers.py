from rest_framework import serializers
from .models import SystemSetting


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
