from datetime import timedelta
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from appointments.models import Appointment

class Command(BaseCommand):
    help = "Send reminders for confirmed appointments today/tomorrow; schedule this command externally."
    def handle(self, *args, **options):
        dates = [timezone.localdate(), timezone.localdate() + timedelta(days=1)]
        qs = Appointment.objects.filter(status=Appointment.Status.CONFIRMED, appointment_date__in=dates).select_related("patient", "doctor__user")
        sent = 0
        for appt in qs:
            if not appt.patient.email: continue
            try:
                send_mail("MediConnect appointment reminder",
                    f"Reminder: your appointment with Dr. {appt.doctor.user.get_full_name() or appt.doctor.user.username} is scheduled for {appt.appointment_date} at {appt.start_time}. Reference: {appt.reference}.",
                    settings.DEFAULT_FROM_EMAIL, [appt.patient.email], fail_silently=False)
                sent += 1
            except Exception as exc:
                self.stderr.write(f"Could not send reminder for appointment {appt.pk}: {exc}")
        self.stdout.write(self.style.SUCCESS(f"Reminder command finished; sent {sent} email(s)."))
