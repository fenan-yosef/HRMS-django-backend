from django.db import models
from django.conf import settings
from core.models import SoftDeleteModel

class EmployeeProfile(SoftDeleteModel):
	"""Normalized employee profile separate from auth user.

	Keeps HR-specific, mutable profile data out of the auth model so
	authentication and profile management are decoupled. This makes
	the schema easier to extend and maintain.
	"""

	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
	job_title = models.CharField(max_length=150, blank=True, null=True)
	phone_number = models.CharField(max_length=30, blank=True, null=True)
	date_of_birth = models.DateField(null=True, blank=True)
	start_date = models.DateField(null=True, blank=True)
	end_date = models.DateField(null=True, blank=True)
	supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="subordinates")
	# additional normalized fields can be added here (address, emergency contact, etc.)

	class Meta:
		verbose_name = "Employee Profile"
		verbose_name_plural = "Employee Profiles"

	def __str__(self):
		return f"Profile: {self.user}"

