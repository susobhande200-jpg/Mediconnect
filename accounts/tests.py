from django.test import TestCase
from django.urls import reverse

class RegistrationPageTests(TestCase):
    def test_registration_page_loads(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)


from django.contrib.auth.models import User
from .models import StaffProfile

class RoleDashboardTests(TestCase):
    def test_nurse_role_has_separate_dashboard(self):
        user = User.objects.create_user(username="nurse_demo", password="Safe-pass-12345")
        StaffProfile.objects.create(user=user, role=StaffProfile.Role.NURSE, is_approved=True)
        self.client.force_login(user)
        response = self.client.get(reverse("staff_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nurse / Medical Staff")

    def test_pharmacist_role_has_separate_dashboard(self):
        user = User.objects.create_user(username="pharmacy_demo", password="Safe-pass-12345")
        StaffProfile.objects.create(user=user, role=StaffProfile.Role.PHARMACIST, is_approved=True)
        self.client.force_login(user)
        response = self.client.get(reverse("staff_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pharmacy dashboard")

    def test_control_center_requires_staff(self):
        user = User.objects.create_user(username="regular_demo", password="Safe-pass-12345")
        self.client.force_login(user)
        response = self.client.get(reverse("control_center"))
        self.assertEqual(response.status_code, 403)
