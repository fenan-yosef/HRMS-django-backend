# HRMS Django Backend Documentation

## Project Overview

This project is a Django-based REST API for a Human Resource Management System (HRMS). It provides endpoints for managing departments, employees, leave requests, and performance reviews. The API is designed to be used by a frontend application for HR management tasks.

## Setup Instructions

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd hrms_backend
    ```

2.  **Create a virtual environment:**

    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**

    *   On Windows:

        ```bash
        venv\Scripts\activate
        ```

    *   On macOS and Linux:

        ```bash
        source venv/bin/activate
        ```

4.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure the database:**

    *   The project uses SQLite by default. You can modify the database settings in `hrms_backend/settings.py`.
    *   To use a different database, update the `DATABASES` setting accordingly.

6.  **Run migrations:**

    ```bash
    python manage.py migrate
    ```

7.  **Create a superuser:**

    ```bash
    python manage.py createsuperuser
    ```

8.  **Run the development server:**

    ```bash
    python manage.py runserver
    ```

## API Endpoints

The API endpoints are defined using Django REST Framework's `DefaultRouter`. The base URL for all API endpoints is `/api/`.

### Departments

*   **`/api/departments/`**
    *   `GET`: List all departments.
    *   `POST`: Create a new department (Admin only).
*   **`/api/departments/{id}/`**
    *   `GET`: Retrieve a specific department.
    *   `PUT/PATCH`: Update a department (Admin only).
    *   `DELETE`: Delete a department (Admin only).

### Employees

*   **`/api/employees/`**
    *   `GET`: List all employees.
    *   `POST`: Create a new employee (Admin only).
*   **`/api/employees/{id}/`**
    *   `GET`: Retrieve a specific employee.
    *   `PUT/PATCH`: Update an employee (Employee themselves or Admin).
    *   `DELETE`: Delete an employee (Admin only).

### Leaves

*   **`/api/leaves/`**
    *   `GET`: List all leave requests (Admin), leave requests for the user and their direct reports (Manager), or the user's own leave requests (Employee).
    *   `POST`: Create a new leave request (Employee).
*   **`/api/leaves/{id}/`**
    *   `GET`: Retrieve a specific leave request.
    *   `PUT/PATCH`: Update a leave request (Employee themselves or Admin).
    *   `DELETE`: Delete a leave request (Employee themselves or Admin).

### Performance Reviews

*   **`/api/reviews/`**
    *   `GET`: List all performance reviews (Admin), reviews for the user's reports (Manager), or the user's own reviews (Employee).
    *   `POST`: Create a new performance review (Admin or Manager).
*   **`/api/reviews/{id}/`**
    *   `GET`: Retrieve a specific performance review.
    *   `PUT/PATCH`: Update a performance review (Admin or Manager).
    *   `DELETE`: Delete a performance review (Admin).

## Models

### Department

*   `id`: Integer (Primary Key)
*   `name`: CharField (Max Length: 100)
*   `location`: CharField (Max Length: 100)

### Employee

*   `id`: Integer (Primary Key)
*   `first_name`: CharField (Max Length: 100)
*   `last_name`: CharField (Max Length: 100)
*   `date_of_birth`: DateField
*   `gender`: CharField (Max Length: 20)
*   `email`: EmailField
*   `phone_number`: CharField (Max Length: 20)
*   `address`: TextField
*   `hire_date`: DateField
*   `job_title`: CharField (Max Length: 100)
*   `status`: CharField (Max Length: 20)
*   `department`: ForeignKey (Department)
*   `manager`: ForeignKey (Employee, null=True, blank=True)

### Leave

*   `id`: Integer (Primary Key)
*   `employee`: ForeignKey (Employee)
*   `start_date`: DateField
*   `end_date`: DateField
*   `leave_type`: CharField (Max Length: 50)
*   `reason`: TextField
*   `status`: CharField (Max Length: 20)

### PerformanceReview

*   `id`: Integer (Primary Key)
*   `employee`: ForeignKey (Employee)
*   `reviewer`: ForeignKey (Employee)
*   `review_date`: DateField
*   `performance_summary`: TextField
*   `rating`: Integer

## Serializers

Serializers are used to convert model instances to JSON format and vice versa.

### DepartmentSerializer

Serializes `Department` objects. Includes `id`, `name`, and `location` fields.

### EmployeeListSerializer

A simplified serializer for listing employees. Includes `id`, `first_name`, `last_name`, `job_title`, `email`, and `department` fields.

### EmployeeDetailSerializer

A detailed serializer for a single employee view. Includes all employee fields, as well as nested `DepartmentSerializer` and `StringRelatedField` for the manager and reports.

### LeaveSerializer

Serializes `Leave` objects. Includes all fields from the `Leave` model.

### PerformanceReviewSerializer

Serializes `PerformanceReview` objects. Includes all fields from the `PerformanceReview` model.

## Permissions

Custom permissions are used to control access to different resources.

### IsAdminOrReadOnly

Allows read-only access to all users, but only allows admin users to modify objects.

### IsManagerAndOwnerOrReadOnly

Allows managers to view their team's data and employees to view their own data. Only the owner of the object can modify it.

### IsEmployeeOwner

Allows users to view any profile (for company directory) but only edit their own.

## Views

### DepartmentViewSet

Provides CRUD operations for `Department` objects. Only admin users can create, update, or delete departments.

### EmployeeViewSet

Provides CRUD operations for `Employee` objects. Anyone can list employees, but only the employee themselves or an admin can edit their profile.

### LeaveViewSet

Provides CRUD operations for `Leave` objects. Employees can only manage their own leave requests, managers can view their team's requests, and admins can see all requests.

### PerformanceReviewViewSet

Provides CRUD operations for `PerformanceReview` objects. Permissions follow the same logic as Leave requests.

## URLs

The URL patterns are defined in `HR/urls.py` and are automatically generated by the `DefaultRouter`.

*   `/api/departments/`: Maps to the `DepartmentViewSet`.
*   `/api/employees/`: Maps to the `EmployeeViewSet`.
*   `/api/leaves/`: Maps to the `LeaveViewSet`.
*   `/api/reviews/`: Maps to the `PerformanceReviewViewSet`.

## Troubleshooting

If you encounter an error like "OperationalError: no such table: hr_department" (or similar for other models like `hr_attendance`), it means the database tables have not been created or are out of date. This can happen after adding a new model to `hr/models.py`.

In this case, ensure you run the following commands to create and apply migrations:

```bash
python manage.py makemigrations hr
python manage.py migrate
```

This will create the necessary tables for all models in the `hr` app, including `Department`, `LeaveRequest`, `PerformanceReview`, and `Attendance`.
