from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.core import signing
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.models import User
from .forms import PatientRegistrationForm
from .models import PatientProfile, StaffProfile
from appointments.models import Appointment, ConsultationNote, Prescription, MedicalRecord

def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            token = signing.dumps({"user_id": user.pk}, salt="mediconnect-email-verification")
            verify_url = request.build_absolute_uri(reverse("verify_email", args=[token]))
            try:
                send_mail("Verify your MediConnect email", f"Hello {user.first_name},\n\nVerify your email by opening:\n{verify_url}\n\nIf you did not create this account, ignore this email.", settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
                messages.success(request, "Account created. Check your email for the verification link.")
            except Exception:
                messages.warning(request, "Account created, but email delivery is not configured. Ask the administrator to configure SMTP.")
            login(request, user)
            return redirect("dashboard")
    else:
        form = PatientRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})

def verify_email(request, token):
    try:
        data = signing.loads(token, salt="mediconnect-email-verification", max_age=60*60*24)
        user = get_object_or_404(User, pk=data["user_id"])
        profile, _ = PatientProfile.objects.get_or_create(user=user)
        profile.email_verified = True
        profile.save(update_fields=["email_verified"])
        messages.success(request, "Email verified successfully.")
    except (signing.BadSignature, signing.SignatureExpired, KeyError, TypeError):
        messages.error(request, "This verification link is invalid or has expired.")
    return redirect("login")

@login_required
def dashboard(request):
    appointments = Appointment.objects.filter(patient=request.user).select_related("doctor__user", "doctor__department").order_by("-appointment_date", "-start_time")
    records = MedicalRecord.objects.filter(patient=request.user).order_by("-created_at")[:5]
    prescriptions = Prescription.objects.filter(patient=request.user).order_by("-created_at")[:5]
    return render(request, "accounts/dashboard.html", {"appointments": appointments[:10], "total_appointments": appointments.count(), "records": records, "prescriptions": prescriptions})

@login_required
def role_dashboard(request):
    profile = getattr(request.user, "staff_profile", None)
    if not request.user.is_staff and not profile:
        messages.error(request, "This dashboard is for authorized clinic staff.")
        return redirect("dashboard")
    if request.user.is_staff:
        return redirect("/admin/")
    if not profile.is_approved:
        return render(request, "accounts/staff_pending.html", {"profile": profile})
    if profile.role == StaffProfile.Role.DOCTOR:
        appointments = Appointment.objects.filter(doctor__user=request.user).select_related("patient", "doctor__department").order_by("appointment_date", "start_time")
        return render(request, "accounts/doctor_dashboard.html", {"appointments": appointments})
    appointments = Appointment.objects.filter(status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED]).select_related("patient", "doctor__user").order_by("appointment_date", "start_time")
    return render(request, "accounts/reception_dashboard.html", {"appointments": appointments})
