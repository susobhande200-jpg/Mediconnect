import uuid
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import DoctorProfile

class Appointment(models.Model):
    class Type(models.TextChoices):
        IN_PERSON = "in_person", "In-person"
        ONLINE = "online", "Online video"
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        REJECTED = "rejected", "Rejected"
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.PROTECT, related_name="appointments")
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    appointment_type = models.CharField(max_length=20, choices=Type.choices, default=Type.IN_PERSON)
    reason = models.TextField(max_length=1000, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    meet_url = models.URLField(blank=True)
    calendar_event_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ("-appointment_date", "-start_time")
        indexes = [models.Index(fields=("doctor", "appointment_date", "start_time"))]
    def clean(self):
        if self.appointment_date and self.appointment_date < timezone.localdate():
            raise ValidationError("Appointments cannot be booked in the past.")
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError("End time must be later than start time.")
        if self.doctor_id and self.appointment_date and self.start_time and self.end_time:
            clashes = Appointment.objects.filter(doctor=self.doctor, appointment_date=self.appointment_date,
                status__in=[self.Status.PENDING, self.Status.CONFIRMED],
                start_time__lt=self.end_time, end_time__gt=self.start_time)
            if self.pk: clashes = clashes.exclude(pk=self.pk)
            if clashes.exists(): raise ValidationError("This doctor already has an appointment overlapping that time.")
    def __str__(self): return f"{self.reference} - {self.patient} / {self.doctor}"

class MedicalRecord(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="medical_records")
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.PROTECT, related_name="medical_records")
    appointment = models.ForeignKey(Appointment, null=True, blank=True, on_delete=models.SET_NULL, related_name="medical_records")
    title = models.CharField(max_length=180)
    record_type = models.CharField(max_length=80, default="Consultation")
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f"{self.title} — {self.patient}"

class ConsultationNote(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name="consultation_note")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    symptoms = models.TextField(blank=True)
    examination = models.TextField(blank=True)
    assessment = models.TextField(blank=True)
    treatment_plan = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    finalized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Prescription(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="prescriptions")
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.PROTECT, related_name="prescriptions")
    appointment = models.ForeignKey(Appointment, null=True, blank=True, on_delete=models.SET_NULL, related_name="prescriptions")
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Prescription #{self.pk} for {self.patient}"

class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="items")
    medication_name = models.CharField(max_length=160)
    dosage = models.CharField(max_length=100)
    route = models.CharField(max_length=80, blank=True)
    frequency = models.CharField(max_length=120)
    duration = models.CharField(max_length=120)
    notes = models.CharField(max_length=250, blank=True)

class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUND_REQUESTED = "refund_requested", "Refund requested"
        REFUNDED = "refunded", "Refunded"
    appointment = models.ForeignKey(Appointment, on_delete=models.PROTECT, related_name="payments")
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING)
    provider = models.CharField(max_length=30, default="demo")
    provider_reference = models.CharField(max_length=180, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f"Payment {self.pk}: {self.status}"

class ChatMessage(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="chat_messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sent_clinic_messages")
    body = models.TextField(max_length=2000)
    shared_meet_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    class Meta: ordering = ["created_at"]
    def __str__(self): return f"Message for appointment {self.appointment_id}"
