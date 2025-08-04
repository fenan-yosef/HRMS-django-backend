
# HRMS Django Backend API Documentation

## Overview
This backend provides a RESTful API for managing users, departments, leave requests, performance reviews, and attendance. Authentication is via JWT. All endpoints require authentication unless noted.

## Setup
1. Clone the repo and install dependencies
2. Add your `.env` file (see example in repo)
3. Run migrations: `python manage.py migrate`
4. Start the server: `python manage.py runserver`

## Authentication
All requests require a JWT token in the `Authorization: Bearer <token>` header.

### Register User
**POST** `/api/auth/register/`
Creates a new user. If no password is provided, a random password is generated and emailed to the user.
**Payload:**
```json
{
  "username": "hr_manager",
  "email": "hr_manager@example.com",
  "password": "your_password", // optional
  "role": "HR"
}
```
**Response:**
```json
{
  "message": "User registered successfully and email sent.",
  "user": {
    "id": 1,
    "username": "hr_manager",
    "email": "hr_manager@example.com",
    "role": "HR"
  }
}
```

### Login & Token
**POST** `/api/auth/token/`
**Payload:**
```json
{
  "email": "hr_manager@example.com",
  "password": "your_password"
}
```
**Response:**
```json
{
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}
```

**POST** `/api/auth/token/refresh/`
**Payload:**
```json
{
  "refresh": "<refresh_token>"
}
```
**Response:**
```json
{
  "access": "<new_access_token>"
}
```

### Get Current User
**GET** `/api/auth/me/`
Returns the authenticated user's profile.
**Response:**
```json
{
  "id": 1,
  "username": "hr_manager",
  "email": "hr_manager@example.com",
  "role": "HR"
}
```

## Users
**GET** `/api/users/` — List all users
**POST** `/api/users/` — Create user (CEO/HR only)
**GET/PUT/PATCH/DELETE** `/api/users/{id}/` — Retrieve, update, or delete user (CEO/HR only)

**Sample User Payload:**
```json
{
  "username": "new_employee",
  "email": "employee@example.com",
  "password": "new_password",
  "role": "Employee"
}
```

**Sample User Response (Employee):**
```json
{
  "id": 3,
  "username": "new_employee",
  "email": "employee@example.com",
  "role": "Employee",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "123-456-7890",
  "is_active": true
}
```

**Sample User Response (Non-Employee):**
```json
{
  "id": 2,
  "username": "hr_manager",
  "email": "hr_manager@example.com",
  "role": "HR",
  "first_name": "Alice",
  "last_name": "Smith",
  "phone_number": "987-654-3210",
  "is_active": true
}
```

## Departments
**GET** `/api/departments/` — List departments
**POST** `/api/departments/` — Create department
**GET/PUT/PATCH/DELETE** `/api/departments/{id}/` — Retrieve, update, or delete department

**Sample Department Payload:**
```json
{
  "name": "Marketing",
  "code": "MKT001",
  "description": "Handles market research and campaigns",
  "manager": 2
}
```
**Sample Department Response:**
```json
{
  "id": 1,
  "name": "Marketing",
  "code": "MKT001",
  "description": "Handles market research and campaigns",
  "manager": 2
}
```

## Leave Requests
**GET** `/api/leave-requests/` — List leave requests (CEO/HR/Manager see all, Employee sees own)
**POST** `/api/leave-requests/` — Create leave request
**GET/PUT/PATCH/DELETE** `/api/leave-requests/{id}/` — Retrieve, update, or delete leave request

**Sample Leave Request Payload:**
```json
{
  "start_date": "2025-07-10",
  "end_date": "2025-07-15",
  "reason": "Family emergency"
}
```
**Sample Leave Request Response:**
```json
{
  "id": 2,
  "employee": 3,
  "start_date": "2025-07-10",
  "end_date": "2025-07-15",
  "status": "Pending",
  "applied_date": "2025-06-25T08:00:00Z"
}
```

## Performance Reviews
**GET** `/api/performance-reviews/` — List reviews (CEO/HR/Manager see all, Employee sees own)
**POST** `/api/performance-reviews/` — Create review (CEO/HR/Manager only)
**GET/PUT/PATCH/DELETE** `/api/performance-reviews/{id}/` — Retrieve, update, or delete review

**Sample Review Payload:**
```json
{
  "employee": 3,
  "reviewer": 2,
  "score": 90,
  "comments": "Excellent work!"
}
```
**Sample Review Response:**
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

## Attendance
**GET** `/api/attendances/` — List attendance records (CEO/HR see all, Manager/Employee see own)
**POST** `/api/attendances/` — Create attendance (CEO/HR only)
**GET/PUT/PATCH/DELETE** `/api/attendances/{id}/` — Retrieve, update, or delete attendance (CEO/HR only)

**Sample Attendance Payload:**
```json
{
  "employee": 3,
  "date": "2025-07-04",
  "status": "Present",
  "check_in_time": "09:00:00",
  "check_out_time": "17:00:00"
}
```
**Sample Attendance Response:**
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

## Permissions
- CEO, HR, Manager, Employee roles are enforced for sensitive actions (see backend code for details)
- Most write actions (create/update/delete) require CEO/HR/Manager
- Employees can only view or update their own records

## Notes
- All endpoints require JWT authentication unless noted
- Registration sends password by email if not provided
- All responses are JSON
- For more details, see the backend code or ask the backend team
