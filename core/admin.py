from django.contrib import admin
from .models import SystemSetting

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'int_value', 'decimal_value', 'updated_at')
    search_fields = ('key',)
