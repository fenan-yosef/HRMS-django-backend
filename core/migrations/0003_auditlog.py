from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

	dependencies = [
		('hr', '0011_complaint'),
		('core', '0002_alter_systemsetting_options'),
	]

	operations = [
		migrations.CreateModel(
			name='AuditLog',
			fields=[
				('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
				('timestamp', models.DateTimeField(auto_now_add=True)),
				('action', models.CharField(blank=True, max_length=100)),
				('summary', models.TextField(blank=True)),
				('method', models.CharField(blank=True, max_length=10)),
				('path', models.CharField(blank=True, max_length=500)),
				('status_code', models.IntegerField(blank=True, null=True)),
				('ip_address', models.CharField(blank=True, max_length=100)),
				('user_agent', models.TextField(blank=True)),
				('target_model', models.CharField(blank=True, max_length=200)),
				('target_object_id', models.CharField(blank=True, max_length=100)),
				('extra', models.JSONField(blank=True, default=dict)),
				('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to='hr.customuser')),
			],
			options={'ordering': ['-timestamp']},
		),
		migrations.AddIndex(
			model_name='auditlog',
			index=models.Index(fields=['timestamp'], name='core_audit_timestamp_idx'),
		),
		migrations.AddIndex(
			model_name='auditlog',
			index=models.Index(fields=['action'], name='core_audit_action_idx'),
		),
	]

