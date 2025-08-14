
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

The performance management feature is now expanded. New models and endpoints are available:

- Review cycles: `/api/review-cycles/`
- Rating scales: `/api/rating-scales/`
- Competencies: `/api/competencies/`
- Performance reviews: `/api/performance-reviews/`
- Review scores (per-competency): `/api/review-scores/` (or nested under a review)
- Review snapshots (immutable copy after finalization): `/api/review-snapshots/`

Access rules: CEO/HR/Manager have broad access; employees may create/view their own self-assessments and view finalized reviews. Detailed permission enforcement is implemented server-side.

Create a review (example): POST `/api/performance-reviews/`
Payload (minimal):
```json
{
  "employee": 3,
  "reviewer": 2,
  "review_cycle": 1,
  "review_type": "annual",
  "self_assessment": "Summary of achievements...",
  "comments": "Manager notes (optional)"
}
```

Response:
```json
{
  "id": 12,
  "employee": 3,
  "reviewer": 2,
  "review_cycle": 1,
  "review_type": "annual",
  "status": "draft",
  "overall_score": null,
  "comments": "Manager notes (optional)",
  "self_assessment": "Summary of achievements...",
  "finalized_at": null,
  "created_at": "2025-08-14T10:00:00Z",
  "updated_at": "2025-08-14T10:00:00Z"
}
```

Add per-competency scores (option A: create via `/api/review-scores/`):
POST `/api/review-scores/`
Payload:
```json
{
  "review": 12,
  "competency": 2,
  "score": 4.5,
  "comment": "Strong communication"
}
```

Response:
```json
{
  "id": 7,
  "review": 12,
  "competency": 2,
  "score": 4.5,
  "comment": "Strong communication"
}
```

Or (option B) if your client supports it, create the review and scores in two requests: create review, then bulk-create scores. When a review is finalized (via POST to `/api/performance-reviews/{id}/finalize/`), the system creates an immutable `ReviewSnapshot` that stores review details and scores.

ReviewCycle endpoints
- **GET** `/api/review-cycles/` — list review cycles
- **POST** `/api/review-cycles/` — create a cycle (HR/Admin)

Sample ReviewCycle payload/response:
```json
POST /api/review-cycles/
{
  "name": "2025 Annual",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "is_active": true
}

Response:
{
  "id": 1,
  "name": "2025 Annual",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "is_active": true
}
```

Competencies & Rating Scales
- **GET/POST** `/api/competencies/` — CRUD competencies
- **GET/POST** `/api/rating-scales/` — CRUD rating scales

Sample Competency payload:
```json
{
  "name": "Communication",
  "description": "Clarity, conciseness and effective feedback",
  "rating_scale": 1
}
```

Review snapshots
- When reviews are finalized they are snapshotted to `/api/review-snapshots/` and become immutable for audit and reporting.

-------------------------

## Goals / OKRs

New endpoints to manage goals and key-results (OKR style):

- **GET/POST** `/api/goals/` — list/create goals
- **GET/PUT/PATCH/DELETE** `/api/goals/{id}/` — manage a single goal
- **GET/POST** `/api/goals/{id}/key-results/` — add/list key-results
- **POST** `/api/goals/{id}/progress/` — post progress updates
- **GET/POST** `/api/goals/{id}/participants/` — assign contributors/watchers

Create a goal (POST `/api/goals/`):
```json
{
  "title": "Increase Quarterly Revenue",
  "description": "Focus on upsell and expansion",
  "owner": 3,
  "creator": 2,
  "department": 1,
  "start_date": "2025-07-01",
  "target_date": "2025-09-30",
  "weight": 1.5,
  "visibility": "team"
}
```

Response:
```json
{
  "id": 5,
  "title": "Increase Quarterly Revenue",
  "owner": 3,
  "status": "open",
  "target_date": "2025-09-30",
  "created_at": "2025-08-14T10:05:00Z"
}
```

Add a Key Result (POST `/api/goals/{id}/key-results/`):
```json
{
  "goal": 5,
  "description": "Increase ARPU by 10%",
  "metric_type": "percent",
  "baseline": 100.0,
  "target": 110.0,
  "current_value": 102.0,
  "unit": "USD"
}
```

Post a progress update (POST `/api/goals/{id}/progress/`):
```json
{
  "goal": 5,
  "updated_by": 3,
  "value": 105.0,
  "note": "Closed several upsell deals"
}
```

Goal participants (POST `/api/goals/{id}/participants/`):
```json
{
  "goal": 5,
  "user": 4,
  "role": "contributor"
}
```

Snapshots: goals can be snapshotted (stored in `/api/goal-snapshots/`) for review-time archival.

-------------------------

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
