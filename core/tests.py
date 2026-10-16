from django.test import TestCase
from django.urls import reverse
from .models import Department

class PublicPagesTests(TestCase):
    def test_homepage_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MediConnect")

    def test_doctor_directory_loads(self):
        response = self.client.get(reverse("doctors"))
        self.assertEqual(response.status_code, 200)
