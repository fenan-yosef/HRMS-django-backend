# Tasks API Documentation

This document describes the Tasks module endpoints, request/response payloads, and role-based permissions.

Base URL prefix: `/api/`

- Tasks: `/api/tasks/`
- Task Comments: `/api/task-comments/`
- Task Attachments: `/api/task-attachments/`
- Task Assignments (history): `/api/task-assignments/`

All endpoints require authentication (Bearer token) unless stated otherwise.

## Roles and access
- CEO/HR (or superuser): Full access to all tasks and related resources across the system.
- Manager: Full CRUD within their department + tasks they created/assigned; read within scope.
- Employee: Read tasks they're assigned to or created; limited update via special actions; can comment and upload attachments on visible tasks.

Note on scoping used by viewsets:
- CEO/HR/superuser: no restriction.
- Manager: department tasks OR tasks they created OR where they are an assignee.
- Employee: tasks they created OR where they are an assignee.

## Task model
```
Task: {
  id: number,
  title: string,
  description?: string,
  creator: number,        // read-only (current user on create)
  assigned_by: number,    // read-only (current user on create)
  assignees: number[],
  department?: number,
  priority: "low"|"medium"|"high"|"critical" (default: "medium"),
  status: "todo"|"in_progress"|"blocked"|"done"|"archived" (default: "todo"),
  due_date?: string (ISO datetime),
  estimate_hours?: string (decimal),
  completed_at?: string (ISO datetime),
  created_at: string,
  updated_at: string
}
```

### Default status on creation
- The default `status` when a new task is created is `"todo"` (as defined in `tasks.models.Task.status` default).

---

## Endpoints: Tasks

### List tasks
GET `/api/tasks/`

Query params:
- `search`: search in `title`, `description`
- `ordering`: one of `due_date`, `priority`, `created_at` (prefix with `-` for desc)

Response: `200 OK` -> `Task[]`

### Retrieve task
GET `/api/tasks/{id}/`

Response: `200 OK` -> `Task`

### Create task
POST `/api/tasks/`

Payload:
```
{
  "title": "Prepare Q3 report",
  "description": "Collect KPIs and compile report",
  "assignees": [3, 8],
  "department": 2,
  "priority": "high",
  "status": "todo",  // optional; defaults to todo
  "due_date": "2025-09-15T17:00:00Z",
  "estimate_hours": "12.5"
}
```

Notes:
- `creator` and `assigned_by` are set automatically to the current user.

Success Response: `201 Created`
```
{
  "id": 42,
  "title": "Prepare Q3 report",
  "description": "Collect KPIs and compile report",
  "creator": 5,
  "assigned_by": 5,
  "assignees": [3, 8],
  "department": 2,
  "priority": "high",
  "status": "todo",
  "due_date": "2025-09-15T17:00:00Z",
  "estimate_hours": "12.50",
  "completed_at": null,
  "created_at": "2025-09-01T09:00:00Z",
  "updated_at": "2025-09-01T09:00:00Z"
}
```

### Update task
PUT/PATCH `/api/tasks/{id}/`

Payload (example PATCH):
```
{
  "title": "Prepare Q3 financial report",
  "priority": "critical",
  "status": "in_progress",
  "due_date": "2025-09-20T17:00:00Z"
}
```

Response: `200 OK` -> updated `Task`

### Delete task
DELETE `/api/tasks/{id}/`

Response: `204 No Content`

---

## Custom actions on Task

### Assign users to a task
POST `/api/tasks/{id}/assign/`

Payload:
```
{ "assignees": [7, 12] }
```

Response:
```
{ "status": "assigned", "assignees": [7, 12, ...existing assignees ids...] }
```

Permissions:
- CEO/HR/managers can assign within scope.

Creates `TaskAssignment` history records per user.

### Unassign users from a task
POST `/api/tasks/{id}/unassign/`

Payload:
```
{ "assignees": [7, 12] }
```

Response:
```
{ "status": "unassigned", "assignees": [ ...remaining assignee ids... ] }
```

### Mark task as done
POST `/api/tasks/{id}/mark_done/`

Response:
```
{ "status": "done", "completed_at": "2025-09-01T10:22:33Z" }
```

---

## Comments

### List comments
GET `/api/task-comments/`

Response: `200 OK` -> `TaskComment[]` (constrained to tasks visible to the user)

### Create comment
POST `/api/task-comments/`

Payload:
```
{ "task": 42, "content": "Please update section 3." }
```

`author` is set automatically.

Response: `201 Created` -> `TaskComment`

### Update/Delete comment
PUT/PATCH/DELETE `/api/task-comments/{id}/`

Permissions follow general visibility and author rules enforced by DRF + project policies.

---

## Attachments

### Upload attachment
POST `/api/task-attachments/` (multipart/form-data)

Fields:
- `task`: number
- `file`: binary file

`uploaded_by` is set automatically.

Response: `201 Created` -> `TaskAttachment`

### List attachments
GET `/api/task-attachments/`

Response: `200 OK` -> `TaskAttachment[]` (scoped like tasks)

---

## Assignment History

### List assignment history
GET `/api/task-assignments/`

Response: `200 OK` -> `TaskAssignment[]`

Object shape:
```
{
  id: number,
  task: number,
  assigned_to: number,
  assigned_by: number | null,
  created_at: string
}
```

---

## Error responses
- `400 Bad Request`: invalid payload (e.g., assignees not list)
- `401 Unauthorized`: missing/invalid token
- `403 Forbidden`: lacks permission (role or scope)
- `404 Not Found`: not visible or does not exist

## Notes
- All datetime fields use ISO 8601.
- Use `?ordering=-created_at` for newest first (default is `-created_at` in model Meta ordering when not overridden by query param).
- File uploads require multipart form.
