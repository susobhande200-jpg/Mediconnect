from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Department, DoctorProfile
from accounts.models import PatientProfile

class Command(BaseCommand):
    help = "Create clearly fictional local demonstration records."
    def handle(self, *args, **options):
        departments = [
            ("General Medicine", "Everyday health concerns and preventive care.", "bi-clipboard2-pulse"),
            ("Cardiology", "Heart health, screening, and cardiovascular care.", "bi-heart-pulse"),
            ("Dermatology", "Skin, hair, and nail health consultations.", "bi-brightness-high"),
            ("Pediatrics", "Healthcare support for children and adolescents.", "bi-balloon-heart"),
            ("Orthopedics", "Bone, joint, and mobility-related care.", "bi-person-walking"),
            ("Mental Wellness", "Supportive mental wellness consultations.", "bi-cloud-sun"),
        ]
        objs = {}
        for name, desc, icon in departments:
            obj, _ = Department.objects.get_or_create(name=name, defaults={"description": desc, "icon": icon})
            objs[name] = obj
        demo_doctors = [
            ("demo_doctor_asha", "Asha", "Sen", "General Medicine", "MBBS, MD", 8, 500),
            ("demo_doctor_rahul", "Rahul", "Das", "Cardiology", "MBBS, MD (Cardiology)", 12, 800),
            ("demo_doctor_mira", "Mira", "Roy", "Dermatology", "MBBS, MD (Dermatology)", 6, 600),
        ]
        for username, first, last, dept, qual, exp, fee in demo_doctors:
            user, created = User.objects.get_or_create(username=username, defaults={"first_name": first, "last_name": last, "email": f"{username}@example.invalid"})
            if created:
                user.set_password("ChangeMe-LocalOnly-123!")
                user.save()
            DoctorProfile.objects.get_or_create(user=user, defaults={"department": objs[dept], "qualification": qual, "experience_years": exp, "consultation_fee": fee, "bio": "Fictional doctor profile for local college-project demonstration.", "is_approved": True})
        patient, created = User.objects.get_or_create(username="demo_patient", defaults={"first_name": "Demo", "last_name": "Patient", "email": "patient@example.invalid"})
        if created:
            patient.set_password("ChangeMe-LocalOnly-123!")
            patient.save()
            PatientProfile.objects.get_or_create(user=patient)
        self.stdout.write(self.style.SUCCESS("Demo data created. Local-only demo password: ChangeMe-LocalOnly-123! Change or remove demo accounts before deployment."))
