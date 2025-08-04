"""
Django management command to migrate Employee data into CustomUser table and update related records.
Run this once, then remove the command and delete the Employee model and related tables via migrations.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

class Command(BaseCommand):
    help = 'Migrate Employee table data to CustomUser and update related models'

    def handle(self, *args, **options):
        from employee.models import Employee as OldEmployee
        from hr.models import CustomUser, PerformanceReview, Attendance

        self.stdout.write(self.style.NOTICE('Starting migration of Employee data...'))

        with transaction.atomic():
            for emp in OldEmployee.objects.all():
                # Create or update CustomUser
                user, created = CustomUser.objects.get_or_create(
                    email=emp.email,
                    defaults={
                        'first_name': emp.first_name,
                        'last_name': emp.last_name,
                        'role': CustomUser.ROLE_CHOICES[2][0],  # 'employee'
                        'job_title': getattr(emp, 'job_title', ''),
                        'phone_number': getattr(emp, 'phone_number', ''),
                        'date_of_birth': getattr(emp, 'date_of_birth', None),
                        'department': getattr(emp, 'department', None),
                        'is_active': emp.is_active,
                    }
                )
                if created:
                    # Use existing hashed password
                    user.password = emp.password
                    user.save()
                    self.stdout.write(self.style.SUCCESS(
                        f'Created CustomUser for {emp.email} (id={user.id})'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'CustomUser already exists for {emp.email} (id={user.id}), updating related records'
                    ))

                # Update related PerformanceReview
                reviews_updated = PerformanceReview.objects.filter(employee_id=emp.id).update(employee=user)
                self.stdout.write(self.style.SUCCESS(
                    f'Updated {reviews_updated} PerformanceReview records for {user.email}'
                ))

                # Update related Attendance
                attendances_updated = Attendance.objects.filter(employee_id=emp.id).update(employee=user)
                self.stdout.write(self.style.SUCCESS(
                    f'Updated {attendances_updated} Attendance records for {user.email}'
                ))

        self.stdout.write(self.style.SUCCESS('Employee to CustomUser migration completed successfully.'))
