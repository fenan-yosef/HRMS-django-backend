from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0010_alter_customuser_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='Complaint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('type', models.CharField(choices=[('manager_report', 'Manager Report'), ('employee_complaint', 'Employee Complaint')], max_length=32)),
                ('subject', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('send_to_ceo', models.BooleanField(default=False)),
                ('status', models.CharField(choices=[('open', 'Open'), ('in_review', 'In Review'), ('resolved', 'Resolved'), ('dismissed', 'Dismissed')], default='open', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='complaints_created', to=settings.AUTH_USER_MODEL)),
                ('target_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='complaints_received', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='complaint',
            index=models.Index(fields=['type', 'status'], name='hr_complain_type_sta_0b1f6a_idx'),
        ),
        migrations.AddIndex(
            model_name='complaint',
            index=models.Index(fields=['created_by'], name='hr_complain_created__bf7681_idx'),
        ),
        migrations.AddIndex(
            model_name='complaint',
            index=models.Index(fields=['target_user'], name='hr_complain_target__0bb167_idx'),
        ),
    ]
