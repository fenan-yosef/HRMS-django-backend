
# HRMS Django Backend API Documentation

## Overview
This backend exposes a REST API for users, departments, leave requests, performance reviews and attendance. Authentication is JWT-based (access + refresh tokens). All endpoints require authentication unless the route explicitly allows public access (register/login/password reset).

## Quick setup
1. Create a virtualenv and install requirements (see `requirements.txt`).
2. Add environment secrets as needed.
3. Run migrations: `python manage.py migrate`.
4. Start dev server: `python manage.py runserver`.

## Base prefixes (routes defined in this repo)
- Main app router mounted at: `/api/`
- Departments mounted at: `/api/departments/`
- Leaves mounted at: `/api/leaves/`

Note: several models exist for review cycles, competencies, rating scales and goals, but there are currently no registered API routes for those models (only `performance-reviews` is routed). If you need endpoints for those models, a viewset/router must be added.

## Authentication
By default use Authorization: Bearer <access_token>. The project exposes both session-like login and JWT token endpoints.

### Register
POST `/api/auth/register/`
Creates a new user. If `password` is omitted a random password is generated and emailed.
Payload (fields supported):
```json
{
  "email": "user@example.com",
  "password": "optional_password",
  "role": "employee",            // optional, case-insensitive
  "first_name": "Alice",
  "last_name": "Smith",
  "phone_number": "+1-555-111-2222",
  "job_title": "Engineer",
  "date_of_birth": "1990-01-01",
  "department": 2                 // department id (optional)
}
```
Response (201):
```json
{
  "message": "User registered successfully and email sent.",
  "user": { "id": 10, "email": "user@example.com", "role": "employee" }
}
```

### Obtain JWT tokens
POST `/api/auth/token/`
Payload:
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```
Response (200):
```json
{
  "access": "<access_token>",
  "refresh": "<refresh_token>",
  "email": "user@example.com",
  "role": "employee"
}
```
Notes: The project uses a custom token serializer that adds `email` and `role` to the token response.

POST `/api/auth/token/refresh/` — refresh access token
Payload: { "refresh": "<refresh_token>" }
Response: { "access": "<new_access_token>" }

### Session-like login (optional)
POST `/api/auth/login/`
Payload:
```json
{
  "identifier": "user@example.com",
  "password": "your_password"
}
```
Response (200):
```json
{ "message": "Login successful.", "email": "user@example.com", "role": "employee" }
```

### Change password
POST `/api/auth/change-password/`
Payload:
```json
{ "old_password": "old", "new_password": "new" }
```

### Password reset
POST `/api/auth/request-password-reset/` — start reset (provide `email`)
POST `/api/auth/reset-password/` — complete reset (see implementation for fields)

### Get current user + dashboard
GET `/api/auth/me/`
Response: serializes the authenticated user via `UserSerializer`. Typical fields returned:
```json
{
  "id": 3,
  "email": "employee@example.com",
  "role": "employee",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "123-456-7890",
  "is_active": true,
  "job_title": "Engineer",
  "date_of_birth": "1990-01-01",
  "department": { "id": 2, "name": "Marketing", "code": "MKT001", "manager": { "id": 5, "first_name": "Mngr" } },
  "dashboard": { /* role-specific metrics may be present */ }
}
```

## Users
Base path: `/api/users/` (registered by router)
- GET `/api/users/` — list users (managers are filtered to their department by the viewset)
- POST `/api/users/` — create user (allowed for CEO/HR/managers per permission logic)
- GET/PUT/PATCH/DELETE `/api/users/{id}/` — detail/update/delete

Payload when creating/updating a user (supported fields):
```json
{
  "email": "employee@example.com",
  "password": "optional",
  "role": "employee",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "123",
  "job_title": "Engineer",
  "date_of_birth": "1990-01-01",
  "department_id": 2        // to set department by id
}
```
Response: returns the serialized user. Example:
```json
{
  "id": 3,
  "email": "employee@example.com",
  "role": "employee",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "123",
  "is_active": true,
  "job_title": "Engineer",
  "date_of_birth": "1990-01-01",
  "department": { "id": 2, "name": "Marketing", "code": "MKT001" }
}
```

Additional user actions (via `users/{id}/promote/` and `users/{id}/demote/` POST actions) exist for role changes (CEO/HR only).

## Departments
Base path: `/api/departments/`
- GET `/api/departments/` — list
- POST `/api/departments/` — create (CEO/HR)
- GET/PUT/PATCH/DELETE `/api/departments/{id}/` — detail/update/delete

Department representation (serializer fields):
```json
{
  "id": 2,
  "name": "Marketing",
  "code": "MKT001",
  "description": "...",
  "manager": { "id": 5, "first_name": "Mngr", "last_name": "Name", "email": "mgr@example.com" },
  "head_count": 12
}
```

## Leave requests
Base path: `/api/leaves/leave-requests/`
- GET `/api/leaves/leave-requests/` — list (employees see their own; HR/CEO see all)
- POST `/api/leaves/leave-requests/` — create
- GET/PUT/PATCH/DELETE `/api/leaves/leave-requests/{id}/` — detail/update/soft-delete

Model/serializer fields (response):
```json
{
  "id": 7,
  "employee": 3,
  "employee_details": { "first_name": "John", "last_name": "Doe", "email": "employee@example.com" },
  "start_date": "2025-07-10",
  "end_date": "2025-07-15",
  "reason": "Family emergency",
  "status": "PENDING",
  "applied_date": "2025-06-25T08:00:00Z",
  "approvers": [ { "id": 5, "first_name": "Mngr", "role": "manager" } ],
  "deleted_by": null,
  "deleted_at": null
}
```
When creating as a normal employee, POST body should include `start_date`, `end_date`, and optional `reason`. HR users may set an explicit `employee` id in the payload.

## Performance reviews
Base path: `/api/performance-reviews/`
- GET `/api/performance-reviews/` — list (CEO/HR/Manager see all; employees see their own)
- POST `/api/performance-reviews/` — create (permissions enforced in viewset)
- GET/PUT/PATCH/DELETE `/api/performance-reviews/{id}/` — detail/update/delete

PerformanceReview fields (example response):
```json
{
  "id": 12,
  "employee": 3,
  "reviewer": 2,
  "review_cycle": null,
  "review_type": "annual",
  "status": "draft",
  "overall_score": null,
  "comments": "Manager notes",
  "self_assessment": "Summary...",
  "finalized_at": null,
  "created_at": "2025-08-14T10:00:00Z",
  "updated_at": "2025-08-14T10:00:00Z"
}
```

Note: Although models exist for review cycles, rating scales, competencies, review scores and snapshots, this codebase currently only registers the `performance-reviews` viewset in the router — there are no public routes for review-cycles/competencies/rating-scales/review-scores/review-snapshots unless you add viewsets/routers for them.

## Attendance
Base path: `/api/attendance/`
- GET `/api/attendance/` — list (CEO/HR get all; managers limited to department; employees get self)
- POST `/api/attendance/` — create (direct CRUD restricted to CEO/HR)
- GET/PUT/PATCH/DELETE `/api/attendance/{id}/` — detail/update/delete (CRUD restricted)

Custom actions:
- POST `/api/attendance/check-in/` — employee check-in (records check_in_time)
- POST `/api/attendance/check-out/` — employee check-out (records check_out_time and computes duration)
- GET `/api/attendance/today/` — fetch today's attendance for the current user
- GET `/api/attendance/monthly-summary/?month=MM&year=YYYY` — monthly summary + stats
- POST `/api/attendance/reset-today/` — admin (CEO/HR) action to reset a user's today attendance. Payload: { "user_id": <id> }

Attendance representation (example):
```json
{
  "id": 2,
  "employee": 3,
  "date": "2025-07-04",
  "status": "Present",
  "check_in_time": "09:00:00",
  "check_out_time": "17:00:00",
  "work_duration": null,        // duration field stored on model (read-only in serializer)
  "total_hours": 8.0,
  "created_at": "2025-07-04T17:07:00Z"
}
```

## Other notes & permissions
- Role-based permissions (CEO/HR/Manager/Employee) are enforced in viewsets. See `hr/permissions.py` for details.
- Soft-delete is used for several models (deleted_at and deleted_by fields present).
- If you want endpoints for review cycles, rating scales, competencies, review scores or the goals/OKR models, add viewsets and register them with the router (they are present as models but not routed).

For implementation details, check the app code under `hr/`, `department/` and `leave/`.
