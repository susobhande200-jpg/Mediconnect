from datetime import date, time, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from core.models import Department, DoctorProfile
from accounts.models import StaffProfile, PatientProfile
from .models import Appointment, ChatMessage, Payment

class AppointmentWorkflowTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="patient_test", password="Test-pass-12345", email="patient@example.com")
        self.doctor_user = User.objects.create_user(username="doctor_test", password="Test-pass-12345", email="doctor@example.com")
        self.reception_user = User.objects.create_user(username="reception_test", password="Test-pass-12345")
        dept = Department.objects.create(name="Test Medicine")
        self.doctor = DoctorProfile.objects.create(user=self.doctor_user, department=dept, qualification="MBBS", is_approved=True)
        StaffProfile.objects.create(user=self.doctor_user, role="doctor", is_approved=True)
        StaffProfile.objects.create(user=self.reception_user, role="receptionist", is_approved=True)
        self.appointment = Appointment.objects.create(patient=self.patient, doctor=self.doctor, appointment_date=date.today()+timedelta(days=2), start_time=time(10), end_time=time(10,30), appointment_type="online")
    def test_end_time_must_be_after_start(self):
        appt = Appointment(patient=self.patient, doctor=self.doctor, appointment_date=date.today()+timedelta(days=3), start_time=time(11), end_time=time(10))
        with self.assertRaises(ValidationError): appt.full_clean()
    def test_patient_cannot_read_other_patient_chat(self):
        other = User.objects.create_user(username="other_patient", password="Test-pass-12345")
        self.client.force_login(other)
        response = self.client.get(reverse("appointment_chat", args=[self.appointment.pk]))
        self.assertEqual(response.status_code, 403)
    def test_patient_can_message_on_own_appointment(self):
        self.client.force_login(self.patient)
        response = self.client.post(reverse("appointment_chat", args=[self.appointment.pk]), {"body":"Can you share the Meet link?", "shared_meet_url":"https://meet.google.com/abc-defg-hij"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ChatMessage.objects.filter(appointment=self.appointment, shared_meet_url__contains="meet.google.com").exists())
    def test_patient_registration_page(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
    def test_patient_cannot_use_staff_dashboard(self):
        self.client.force_login(self.patient)
        response = self.client.get(reverse("staff_dashboard"))
        self.assertEqual(response.status_code, 302)
