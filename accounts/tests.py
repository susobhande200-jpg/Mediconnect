from django.test import TestCase
from django.urls import reverse

class RegistrationPageTests(TestCase):
    def test_registration_page_loads(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
