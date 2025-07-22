# HRMS Django Backend Documentation

## Project Overview

This project is a Django-based REST API for a Human Resource Management System (HRMS) that provides endpoints for managing users, departments, leave requests, performance reviews, and attendance. The API uses JWT for authentication and has role-based access control.

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

5.  **Run migrations:**

    ```bash
    python manage.py migrate
    ```

6.  **Create a superuser (optional, for admin panel access):**

    ```bash
    python manage.py createsuperuser
    ```

7.  **Run the development server:**

    ```bash
    python manage.py runserver
    ```

## API Endpoints

Base URL: `/api/`

---

### Authentication

#### 1. Register User
**Endpoint:** `POST /api/auth/register/`  
**Description:** Create a new user.

**Example Payload:**
```json
{
  "username": "hr_manager",
  "email": "hr_manager@example.com",
  "password": "your_password",
  "role": "HR"
}
```

**Sample Response:**
```json
{
    "message": "User registered successfully.",
    "user": {
        "username": "hr_manager",
        "email": "hr_manager@example.com",
        "role": "HR"
    }
}
```

---

#### 2. Obtain JWT Token
**Endpoint:** `POST /api/auth/token/`  
**Description:** Obtain JWT access and refresh tokens.

**Note:** The authentication process checks both the `CustomUser` and `Employee` models.

**Example Payload:**
```json
{
  "email": "hr_manager",
  "password": "your_password"
}
```

**Sample Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJh...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJh..."
}
```

---

#### 3. Refresh JWT Token
**Endpoint:** `POST /api/auth/token/refresh/`  
**Description:** Refresh an expired access token.

**Example Payload:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJh..."
}
```

**Sample Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJh..."
}
```

---

#### 4. Get CSRF Token
**Endpoint:** `GET /api/get-csrf-token/`  
**Description:** Retrieve a CSRF token (if needed).

**Sample Response:**  
An HTML template displaying the CSRF token.

---

### Users

#### 1. List Users
**Endpoint:** `GET /api/users/`  
**Description:** Retrieve a list of all users.  
**Authentication:** Any authenticated user.

**Sample Response:**
```json
[
  {
    "id": 1,
    "username": "ceo_user",
    "email": "ceo@example.com",
    "role": "CEO"
  },
  {
    "id": 2,
    "username": "hr_manager",
    "email": "hr_manager@example.com",
    "role": "HR"
  }
]
```

#### 2. Create User
**Endpoint:** `POST /api/users/`  
**Description:** Create a new user (accessible only by CEO or HR).  
**Example Payload:**
```json
{
  "username": "new_employee",
  "email": "employee@example.com",
  "password": "new_password",
  "role": "Employee"
}
```

**Sample Response:**
```json
{
  "id": 3,
  "username": "new_employee",
  "email": "employee@example.com",
  "role": "Employee"
}
```

#### 3. Retrieve/Update/Delete User
**Endpoint:** `/api/users/{id}/`  
**Description:**  
- `GET`: Retrieve details for a user.  
- `PUT/PATCH`: Update user details (CEO or HR only).  
- `DELETE`: Delete a user (CEO or HR only).

**Example GET Response:**
```json
{
  "id": 2,
  "username": "hr_manager",
  "email": "hr_manager@example.com",
  "role": "HR"
}
```

---

### Departments

#### 1. List Departments
**Endpoint:** `GET /api/departments/`  
**Description:** Retrieve all departments.  
**Sample Response:**
```json
[
  {
    "id": 1,
    "name": "Engineering",
    "code": "ENG001",
    "description": "Handles product development",
    "manager": 2
  }
]
```

#### 2. Create Department
**Endpoint:** `POST /api/departments/`  
**Description:** Create a new department.  
**Example Payload:**
```json
{
  "name": "Marketing",
  "code": "MKT001",
  "description": "Handles market research and campaigns"
}
```

#### 3. Retrieve/Update/Delete Department
**Endpoint:** `/api/departments/{id}/`  
**Description:**  
- `GET`: Retrieve department details.  
- `PUT/PATCH`: Update department details.  
- `DELETE`: Delete a department.
**Permissions:** Authenticated users only.

**Example GET Response:**
```json
{
  "id": 1,
  "name": "Engineering",
  "code": "ENG001",
  "description": "Handles product development",
  "manager": 2
}
```

---

### Leave Requests

#### 1. List Leave Requests
**Endpoint:** `GET /api/leave-requests/`  
**Description:**  
- For CEO/HR/Manager: Returns all leave requests.  
- For Employee: Returns only their own leave requests.

**Sample Response for CEO:**
```json
[
  {
    "id": 1,
    "employee": 3,
    "start_date": "2025-07-01",
    "end_date": "2025-07-05",
    "status": "Pending",
    "created_at": "2025-06-20T12:34:56Z"
  }
]
```

#### 2. Create Leave Request
**Endpoint:** `POST /api/leave-requests/`  
**Description:** Employees create a new leave request (employee field auto-assigned).  
**Example Payload:**
```json
{
  "start_date": "2025-07-10",
  "end_date": "2025-07-15"
}
```

**Sample Response:**
```json
{
  "id": 2,
  "employee": 3,
  "start_date": "2025-07-10",
  "end_date": "2025-07-15",
  "status": "Pending",
  "created_at": "2025-06-25T08:00:00Z"
}
```

#### 3. Retrieve/Update/Delete Leave Request
**Endpoint:** `/api/leave-requests/{id}/`  
**Description:**  
- `GET`: Retrieve leave request details.  
- `PUT/PATCH`: Update (accessible by owner, CEO, HR, or Manager).  
- `DELETE`: Delete (accessible by owner, CEO, HR, or Manager).

**Example GET Response:**
```json
{
  "id": 1,
  "employee": 3,
  "start_date": "2025-07-01",
  "end_date": "2025-07-05",
  "status": "Pending",
  "created_at": "2025-06-20T12:34:56Z"
}
```

---

### Performance Reviews

#### 1. List Performance Reviews
**Endpoint:** `GET /api/performance-reviews/`  
**Description:**  
- For CEO/HR/Manager: Returns all performance reviews.  
- For Employee: Returns only their own reviews.

**Sample Response:**
```json
[
  {
    "id": 1,
    "employee": 3,
    "reviewer": 2,
    "score": 85,
    "comments": "Good performance overall.",
    "created_at": "2025-06-15T10:20:30Z"
  }
]
```

#### 2. Create Performance Review
**Endpoint:** `POST /api/performance-reviews/`  
**Description:** Create a new review (accessible only by CEO, HR, or Manager).  
**Example Payload:**
```json
{
  "employee": 3,
  "reviewer": 2,
  "score": 90,
  "comments": "Excellent work!"
}
```

**Sample Response:**
```json
{
  "id": 2,
  "employee": 3,
  "reviewer": 2,
  "score": 90,
  "comments": "Excellent work!",
  "created_at": "2025-06-28T14:45:00Z"
}
```

#### 3. Retrieve/Update/Delete Performance Review
**Endpoint:** `/api/performance-reviews/{id}/`  
**Description:**  
- `GET`: Retrieve review details.  
- `PUT/PATCH`: Update review (CEO, HR, or Manager only).  
- `DELETE`: Delete review (CEO, HR, or Manager only).

**Example GET Response:**
```json
{
  "id": 1,
  "employee": 3,
  "reviewer": 2,
  "score": 85,
  "comments": "Good performance overall.",
  "created_at": "2025-06-15T10:20:30Z"
}
```

---

### Attendance

#### 1. List Attendance Records
**Endpoint:** `GET /api/attendances/`  
**Description:**  
- For CEO/HR: Returns all attendance records.  
- For Manager/Employee: Returns only their own records.

**Sample Response:**
```json
[
  {
    "id": 1,
    "employee": 3,
    "date": "2025-07-04",
    "status": "Present",
    "check_in_time": "09:00:00",
    "check_out_time": "17:00:00",
    "created_at": "2025-07-04T17:05:00Z"
  }
]
```

#### 2. Create Attendance Record
**Endpoint:** `POST /api/attendances/`  
**Description:** Create a new attendance record (accessible only by CEO or HR).  
**Example Payload:**
```json
{
  "employee": 3,
  "date": "2025-07-04",
  "status": "Present",
  "check_in_time": "09:00:00",
  "check_out_time": "17:00:00"
}
```

**Sample Response:**
```json
{
  "id": 2,
  "employee": 3,
  "date": "2025-07-04",
  "status": "Present",
  "check_in_time": "09:00:00",
  "check_out_time": "17:00:00",
  "created_at": "2025-07-04T17:07:00Z"
}
```

#### 3. Retrieve/Update/Delete Attendance Record
**Endpoint:** `/api/attendances/{id}/`  
**Description:**  
- `GET`: Retrieve attendance details.  
- `PUT/PATCH`: Update attendance (CEO or HR only).  
- `DELETE`: Delete attendance (CEO or HR only).

**Example GET Response:**
```json
{
  "id": 1,
  "employee": 3,
  "date": "2025-07-04",
  "status": "Present",
  "check_in_time": "09:00:00",
  "check_out_time": "17:00:00",
  "created_at": "2025-07-04T17:05:00Z"
}
```

---

### Employees

#### 1. List Employees
**Endpoint:** `GET /api/employees/`  
**Description:** Retrieve a list of all employees.  
**Sample Response:**
```json
[
  {
    "id": 1,
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane.doe@example.com",
    "job_title": "Software Engineer",
    "department": 1,
    "department_details": {
      "id": 1,
      "name": "Engineering",
      "code": "ENG001",
      "description": "Handles product development",
      "manager": 2
    },
    "phone_number": "123-456-7890",
    "date_of_birth": "1990-05-15",
    "date_joined": "2025-07-07",
    "is_active": true
  }
]
```

#### 2. Create Employee
**Endpoint:** `POST /api/employees/`  
**Description:** Create a new employee.  
**Example Payload:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "email": "john.smith@example.com",
  "job_title": "Marketing Manager",
  "department": 2,
  "phone_number": "987-654-3210",
  "date_of_birth": "1985-08-20",
  "is_active": true,
  "password": "optional_custom_password"
}
```
- `department`: Department ID (integer).
- `password`: Optional. If omitted, a default password is set.

**Sample Response:**
```json
{
  "id": 2,
  "first_name": "John",
  "last_name": "Smith",
  "email": "john.smith@example.com",
  "job_title": "Marketing Manager",
  "department": 2,
  "department_details": {
    "id": 2,
    "name": "Marketing",
    "code": "MKT001",
    "description": "Handles market research and campaigns",
    "manager": 4
  },
  "phone_number": "987-654-3210",
  "date_of_birth": "1985-08-20",
  "date_joined": "2025-07-07",
  "is_active": true
}
```

#### 3. Retrieve/Update/Delete Employee
**Endpoint:** `/api/employees/{id}/`  
**Description:**  
- `GET`: Retrieve employee details.  
- `PUT/PATCH`: Update employee details.  
- `DELETE`: Delete an employee.
**Permissions:** Authenticated users only.

**Example GET Response:**
```json
{
  "id": 2,
  "first_name": "John",
  "last_name": "Smith",
  "email": "john.smith@example.com",
  "job_title": "Marketing Manager",
  "department": 2,
  "department_details": {
    "id": 2,
    "name": "Marketing",
    "code": "MKT001",
    "description": "Handles market research and campaigns",
    "manager": 4
  },
  "phone_number": "987-654-3210",
  "date_of_birth": "1985-08-20",
  "date_joined": "2025-07-07",
  "is_active": true
}
```
**Example Update Payload:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "job_title": "Senior Marketing Manager",
  "department": 2,
  "phone_number": "987-654-3210",
  "date_of_birth": "1985-08-20",
  "is_active": true
}
```

**Note:**  
- To update the department, provide the department ID in the `department` field.
- The `department_details` field is read-only and always included in responses.

---

## Departments API

All endpoints require authentication (JWT token in `Authorization: Bearer <token>` header).

### List Departments

**GET** `/api/departments/`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Engineering",
    "code": "ENG001",
    "description": "Handles all engineering tasks.",
    "created_at": "2024-07-21T10:00:00Z",
    "manager": {
      "id": 2,
      "first_name": "Jane",
      "last_name": "Doe"
    }
  },
  {
    "id": 2,
    "name": "Marketing",
    "code": "MKT001",
    "description": "Handles market research and campaigns.",
    "created_at": "2024-07-21T11:00:00Z",
    "manager": null
  }
]
```

### Retrieve Department

**GET** `/api/departments/{id}/`

**Response:**
```json
{
  "id": 1,
  "name": "Engineering",
  "code": "ENG001",
  "description": "Handles all engineering tasks.",
  "created_at": "2024-07-21T10:00:00Z",
  "manager": {
    "id": 2,
    "first_name": "Jane",
    "last_name": "Doe"
  }
}
```

### Create Department

**POST** `/api/departments/`

**Request:**
```json
{
  "name": "Finance",
  "code": "FIN",
  "description": "Handles company finances.",
  "manager": 3
}
```

**Response:**
```json
{
  "id": 2,
  "name": "Finance",
  "code": "FIN",
  "description": "Handles company finances.",
  "created_at": "2024-07-21T11:00:00Z",
  "manager": 3
}
```

### Update Department

**PUT/PATCH** `/api/departments/{id}/`

**Request:**
```json
{
  "name": "Finance & Accounting",
  "description": "Handles all financial and accounting matters."
}
```

**Response:**
```json
{
  "id": 2,
  "name": "Finance & Accounting",
  "code": "FIN",
  "description": "Handles all financial and accounting matters.",
  "created_at": "2024-07-21T11:00:00Z",
  "manager": 3
}
```

### Delete Department

**DELETE** `/api/departments/{id}/`

**Response:**  
HTTP 204 No Content

---


### Department Model Fields

- `id`: integer, auto-generated
- `name`: string, required, max 100 chars
- `code`: string, required, unique, max 10 chars
- `description`: string, optional
- `created_at`: datetime, auto-generated
- `manager`: object (with `id`, `first_name`, `last_name`), or `null`

### Notes

- Only authenticated users can access these endpoints.
- The `manager` field in responses is an object with `id`, `first_name`, and `last_name` (or `null` if not set), matching the API's use of a nested serializer.
- See `department/models.py` and `department/serializers.py` for more details.

---

## Models Overview

- **CustomUser:** Extends Django's AbstractUser and includes a `role` field (CEO, Manager, HR, Employee).  
- **Department:** Contains `name`, `code`, `description`, and a reference to a manager (`CustomUser`).  
- **Employee:** Contains personal and job-related information for employees, and is linked to a `Department`.
- **LeaveRequest:** Tracks leave details with a foreign key to `Employee`, start/end dates, status, and creation time.  
- **PerformanceReview:** Contains review details with a foreign key to `Employee`, `reviewer` (a `CustomUser`), score, comments, and creation time.  
- **Attendance:** Logs attendance with a foreign key to `Employee`, date, status, check-in and check-out times, and creation time.

## Permissions

- **IsCEO:** Only users with the 'CEO' role.
- **IsManager:** Only users with the 'Manager' role.
- **IsHR:** Only users with the 'HR' role.
- **IsEmployee:** Only users with the 'Employee' role.
- **IsOwner:** Permissions granted only to the object owner.
- **AnyOf:** Composite permission that grants access if any included permission returns true.

## Troubleshooting

- If you encounter errors like "OperationalError: no such table: hr_department" or 
  "ProgrammingError: column \"name\" of relation \"django_content_type\" does not exist", ensure you run the migrations:
  
  ```bash
  python manage.py makemigrations
  python manage.py migrate
  ```

- If you see a DuplicateTable error for the hr app (e.g., "relation \"hr_customuser\" already exists"), you can either:
  
  1. Drop the existing hr tables in your database manually, then re-run migrations;  
  2. Or mark the initial HR migrations as applied without executing them:
  
     ```bash
     python manage.py migrate hr zero --fake
     python manage.py migrate --fake-initial
     ```

- If the error persists, you may need to reset the migrations (CAUTION: This will reset your database schema):

```bash
python manage.py migrate contenttypes zero
python manage.py migrate
```

---

*This documentation is updated to reflect all available endpoints, their respective example payloads, and responses for seamless front-end integration.*
