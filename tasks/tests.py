from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from department.models import Department
from .models import Task


class TaskFlowTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.ceo = User.objects.create_user(email="ceo@example.com", password="pass", role="ceo")
        self.hr = User.objects.create_user(email="hr@example.com", password="pass", role="hr")
        self.manager = User.objects.create_user(email="mgr@example.com", password="pass", role="manager")
        self.emp = User.objects.create_user(email="emp@example.com", password="pass", role="employee")
        self.dept = Department.objects.create(name="IT", code="IT", manager=self.manager)
        self.manager.department = self.dept
        self.manager.save(update_fields=["department"])
        self.emp.department = self.dept
        self.emp.save(update_fields=["department"])

    def auth(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_ceo_creates_task_for_dept_and_manager_assigns(self):
        client = self.auth(self.ceo)
        # CEO creates task for IT dept
        res = client.post(
            "/api/tasks/",
            {"title": "Quarterly Report", "department": self.dept.id, "priority": "high"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        task_id = res.data["id"]

        # Manager sees and assigns to employee
        mclient = self.auth(self.manager)
        res2 = mclient.post(
            f"/api/tasks/{task_id}/assign/",
            {"assignees": [self.emp.id]},
            format="json",
        )
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        # Employee can see assigned task
        eclient = self.auth(self.emp)
        res3 = eclient.get("/api/tasks/?ordering=due_date")
        self.assertEqual(res3.status_code, status.HTTP_200_OK)
        data = res3.json()
        items = data.get("results", data)  # handle paginated or non-paginated
        ids = [t["id"] for t in items]
        self.assertIn(task_id, ids)
