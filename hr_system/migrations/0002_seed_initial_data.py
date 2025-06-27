# hr_system/migrations/0002_seed_initial_data.py

from django.db import migrations

def create_initial_data(apps, schema_editor):
    """
    Creates initial data for the HR system, including Departments and Employees.
    """
    Department = apps.get_model('hr_system', 'Department')
    Employee = apps.get_model('hr_system', 'Employee')

    # --- Create Departments ---
    print("\nCreating departments...")
    tech = Department.objects.create(name='Technology', location='Building A, Floor 3')
    hr = Department.objects.create(name='Human Resources', location='Building C, Floor 1')
    sales = Department.objects.create(name='Sales', location='Building B, Floor 2')
    print("Departments created.")

    # --- Create Employees ---
    print("Creating employees...")
    # Create a manager in the Tech department
    manager_ada = Employee.objects.create(
        first_name='Ada',
        last_name='Lovelace',
        date_of_birth='1815-12-10',
        gender='Female',
        email='ada.lovelace@example.com',
        hire_date='2022-01-15',
        department=tech,
        job_title='Engineering Manager',
        salary=95000.00,
        status='Active',
        manager=None  # Ada is a top-level manager
    )

    # Create an employee who reports to Ada
    Employee.objects.create(
        first_name='Charles',
        last_name='Babbage',
        date_of_birth='1791-12-26',
        gender='Male',
        email='charles.babbage@example.com',
        hire_date='2023-03-20',
        department=tech,
        job_title='Software Engineer',
        salary=75000.00,
        status='Active',
        manager=manager_ada
    )
    
    # Create an employee in the HR department
    Employee.objects.create(
        first_name='Grace',
        last_name='Hopper',
        date_of_birth='1906-12-09',
        gender='Female',
        email='grace.hopper@example.com',
        hire_date='2022-05-10',
        department=hr,
        job_title='HR Specialist',
        salary=68000.00,
        status='Active',
        manager=None 
    )

    # Create an employee in the Sales department
    Employee.objects.create(
        first_name='Alan',
        last_name='Turing',
        date_of_birth='1912-06-23',
        gender='Male',
        email='alan.turing@example.com',
        hire_date='2024-01-01',
        department=sales,
        job_title='Sales Associate',
        salary=62000.00,
        status='Active',
        manager=None
    )
    print("Employees created.")


class Migration(migrations.Migration):

    dependencies = [
        ('hr_system', '0001_initial'), # This should match your previous migration file
    ]

    operations = [
        migrations.RunPython(create_initial_data),
    ]
