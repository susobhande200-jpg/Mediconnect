import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("core", "0001_initial")]
    operations = [
        migrations.CreateModel(name="Appointment", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("reference", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ("appointment_date", models.DateField()),
            ("start_time", models.TimeField()),
            ("end_time", models.TimeField()),
            ("appointment_type", models.CharField(choices=[("in_person", "In-person"), ("online", "Online video")], default="in_person", max_length=20)),
            ("reason", models.TextField(blank=True, max_length=1000)),
            ("status", models.CharField(choices=[("pending", "Pending"), ("confirmed", "Confirmed"), ("completed", "Completed"), ("cancelled", "Cancelled"), ("rejected", "Rejected")], default="pending", max_length=20)),
            ("meet_url", models.URLField(blank=True)),
            ("calendar_event_id", models.CharField(blank=True, max_length=255)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("doctor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="appointments", to="core.doctorprofile")),
            ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="appointments", to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ("-appointment_date", "-start_time")}),
        migrations.AddIndex(model_name="appointment", index=models.Index(fields=["doctor", "appointment_date", "start_time"], name="appointmen_doctor__bb7c3a_idx")),
        migrations.CreateModel(name="MedicalRecord", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("title", models.CharField(max_length=180)), ("record_type", models.CharField(default="Consultation", max_length=80)),
            ("summary", models.TextField()), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("appointment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="medical_records", to="appointments.appointment")),
            ("doctor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="medical_records", to="core.doctorprofile")),
            ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="medical_records", to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="ConsultationNote", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("symptoms", models.TextField(blank=True)), ("examination", models.TextField(blank=True)), ("assessment", models.TextField(blank=True)),
            ("treatment_plan", models.TextField(blank=True)), ("follow_up_date", models.DateField(blank=True, null=True)),
            ("finalized", models.BooleanField(default=False)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("appointment", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="consultation_note", to="appointments.appointment")),
            ("author", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="Prescription", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("instructions", models.TextField(blank=True)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("appointment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="prescriptions", to="appointments.appointment")),
            ("doctor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="prescriptions", to="core.doctorprofile")),
            ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="prescriptions", to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="PrescriptionItem", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("medication_name", models.CharField(max_length=160)), ("dosage", models.CharField(max_length=100)), ("route", models.CharField(blank=True, max_length=80)),
            ("frequency", models.CharField(max_length=120)), ("duration", models.CharField(max_length=120)), ("notes", models.CharField(blank=True, max_length=250)),
            ("prescription", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="appointments.prescription")),
        ]),
        migrations.CreateModel(name="Payment", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("amount", models.DecimalField(decimal_places=2, max_digits=9)), ("currency", models.CharField(default="INR", max_length=3)),
            ("status", models.CharField(choices=[("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed"), ("refund_requested", "Refund requested"), ("refunded", "Refunded")], default="pending", max_length=24)),
            ("provider", models.CharField(default="demo", max_length=30)), ("provider_reference", models.CharField(blank=True, max_length=180)),
            ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("appointment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="appointments.appointment")),
            ("patient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="ChatMessage", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("body", models.TextField(max_length=2000)), ("shared_meet_url", models.URLField(blank=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)), ("read_at", models.DateTimeField(blank=True, null=True)),
            ("appointment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chat_messages", to="appointments.appointment")),
            ("sender", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sent_clinic_messages", to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ["created_at"]}),
    ]
