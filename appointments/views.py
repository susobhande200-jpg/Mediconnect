from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from core.models import DoctorProfile
from accounts.models import StaffProfile
from .forms import AppointmentForm, ChatMessageForm, ConsultationNoteForm, PrescriptionForm, PrescriptionItemForm
from .models import Appointment, ChatMessage, ConsultationNote, MedicalRecord, Prescription, PrescriptionItem, Payment

def _staff_role(user):
    profile = getattr(user, "staff_profile", None)
    return profile if profile and profile.is_approved else None

@login_required
def book(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    appointment = form.save(commit=False)
                    appointment.patient = request.user
                    appointment.full_clean()
                    appointment.save()
                messages.success(request, f"Appointment request created. Reference: {appointment.reference}")
                return redirect("dashboard")
            except ValidationError as exc:
                form.add_error(None, exc)
    else:
        form = AppointmentForm(initial={"doctor": request.GET.get("doctor")} if request.GET.get("doctor") else None)
    return render(request, "appointments/book.html", {"form": form})

@login_required
def cancel(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)
    if request.method == "POST" and appointment.status in (Appointment.Status.PENDING, Appointment.Status.CONFIRMED):
        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status"])
        messages.success(request, "Appointment cancelled.")
    return redirect("dashboard")

@login_required
def staff_appointment_action(request, pk, action):
    profile = _staff_role(request.user)
    if not request.user.is_staff and not profile:
        raise PermissionDenied
    if profile and profile.role not in (StaffProfile.Role.DOCTOR, StaffProfile.Role.RECEPTIONIST):
        raise PermissionDenied
    appointment = get_object_or_404(Appointment, pk=pk)
    if profile and profile.role == StaffProfile.Role.DOCTOR and appointment.doctor.user_id != request.user.id:
        raise PermissionDenied
    if request.method != "POST":
        return redirect("staff_dashboard")
    allowed = {
        "confirm": Appointment.Status.CONFIRMED,
        "reject": Appointment.Status.REJECTED,
        "complete": Appointment.Status.COMPLETED,
    }
    if action not in allowed:
        raise PermissionDenied
    if action == "confirm" and appointment.status == Appointment.Status.PENDING:
        appointment.status = allowed[action]
    elif action == "reject" and appointment.status == Appointment.Status.PENDING:
        appointment.status = allowed[action]
    elif action == "complete" and appointment.status == Appointment.Status.CONFIRMED:
        appointment.status = allowed[action]
    else:
        messages.warning(request, "That status change is not allowed.")
        return redirect("staff_dashboard")
    appointment.save(update_fields=["status"])
    if appointment.patient.email:
        try:
            send_mail("MediConnect appointment update", f"Your appointment status is now {appointment.get_status_display()}. Reference: {appointment.reference}", settings.DEFAULT_FROM_EMAIL, [appointment.patient.email], fail_silently=True)
        except Exception:
            pass
    messages.success(request, f"Appointment marked {appointment.get_status_display().lower()}.")
    return redirect("staff_dashboard")

def _can_access_appointment(user, appointment):
    if user.is_superuser:
        return True
    if appointment.patient_id == user.id:
        return True
    profile = _staff_role(user)
    if not profile:
        return False
    if profile.role == StaffProfile.Role.DOCTOR:
        return appointment.doctor.user_id == user.id
    # Receptionists coordinate appointment operations. Nurses/pharmacists are
    # limited to appointments with an existing clinical/dispensing relationship.
    if profile.role == StaffProfile.Role.RECEPTIONIST:
        return True
    if profile.role == StaffProfile.Role.NURSE:
        return appointment.status in (Appointment.Status.CONFIRMED, Appointment.Status.COMPLETED)
    if profile.role == StaffProfile.Role.PHARMACIST:
        return appointment.prescriptions.exists()
    return False

@login_required
def chat(request, pk):
    appointment = get_object_or_404(Appointment.objects.select_related("patient", "doctor__user"), pk=pk)
    if not _can_access_appointment(request.user, appointment):
        raise PermissionDenied
    if request.method == "POST":
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.appointment = appointment
            msg.sender = request.user
            msg.save()
            sender_profile = _staff_role(request.user)
            if request.user.id == appointment.patient_id:
                other = appointment.doctor.user
            elif sender_profile and sender_profile.role == StaffProfile.Role.RECEPTIONIST:
                other = appointment.doctor.user
            else:
                other = appointment.patient
            if other.email:
                send_mail("New MediConnect appointment message", f"You have a new message regarding appointment {appointment.reference}. Sign in to MediConnect to view it.", settings.DEFAULT_FROM_EMAIL, [other.email], fail_silently=True)
            return redirect("appointment_chat", pk=pk)
    else:
        form = ChatMessageForm()
    return render(request, "appointments/chat.html", {"appointment": appointment, "messages_list": appointment.chat_messages.select_related("sender"), "form": form})

@login_required
def clinical_note(request, pk):
    appointment = get_object_or_404(Appointment.objects.select_related("patient", "doctor__user"), pk=pk)
    profile = _staff_role(request.user)
    if not (request.user.is_staff or (profile and profile.role == StaffProfile.Role.DOCTOR and appointment.doctor.user_id == request.user.id)):
        raise PermissionDenied
    note, _ = ConsultationNote.objects.get_or_create(appointment=appointment, defaults={"author": request.user})
    if note.finalized and not request.user.is_staff:
        messages.warning(request, "This note is finalized. Ask an administrator to amend it.")
        return redirect("staff_dashboard")
    if request.method == "POST":
        form = ConsultationNoteForm(request.POST, instance=note)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.save()
            MedicalRecord.objects.create(patient=appointment.patient, doctor=appointment.doctor, appointment=appointment,
                title=f"Consultation note — {appointment.appointment_date}", record_type="Consultation", summary=obj.assessment or obj.treatment_plan or "Consultation record")
            messages.success(request, "Clinical note saved.")
            return redirect("staff_dashboard")
    else:
        form = ConsultationNoteForm(instance=note)
    return render(request, "appointments/clinical_note.html", {"form": form, "appointment": appointment})

@login_required
def create_prescription(request, pk):
    appointment = get_object_or_404(Appointment.objects.select_related("patient", "doctor__user"), pk=pk)
    profile = _staff_role(request.user)
    if not (request.user.is_staff or (profile and profile.role == StaffProfile.Role.DOCTOR and appointment.doctor.user_id == request.user.id)):
        raise PermissionDenied
    if request.method == "POST":
        form = PrescriptionForm(request.POST)
        item_form = PrescriptionItemForm(request.POST)
        if form.is_valid() and item_form.is_valid():
            with transaction.atomic():
                prescription = form.save(commit=False)
                prescription.patient = appointment.patient
                prescription.doctor = appointment.doctor
                prescription.appointment = appointment
                prescription.save()
                item = item_form.save(commit=False)
                item.prescription = prescription
                item.save()
            messages.success(request, "Prescription saved.")
            return redirect("staff_dashboard")
    else:
        form, item_form = PrescriptionForm(), PrescriptionItemForm()
    return render(request, "appointments/prescription_form.html", {"form": form, "item_form": item_form, "appointment": appointment})

@login_required
def request_payment(request, pk):
    appointment = get_object_or_404(Appointment.objects.select_related("doctor", "patient"), pk=pk, patient=request.user)
    if request.method == "POST":
        amount = appointment.doctor.consultation_fee
        payment = Payment.objects.create(appointment=appointment, patient=request.user, amount=amount, provider="demo")
        messages.info(request, f"Demo payment record #{payment.pk} created. No money was charged.")
        return redirect("dashboard")
    return render(request, "appointments/payment.html", {"appointment": appointment})

@login_required
def payment_action(request, pk, action):
    payment = get_object_or_404(Payment.objects.select_related("appointment"), pk=pk)
    profile = _staff_role(request.user)
    is_owner = payment.patient_id == request.user.id
    if not (request.user.is_staff or is_owner):
        raise PermissionDenied
    if request.method != "POST":
        return redirect("dashboard")
    if action == "refund-request" and is_owner and payment.status == Payment.Status.PAID:
        payment.status = Payment.Status.REFUND_REQUESTED
        payment.save(update_fields=["status", "updated_at"])
        messages.success(request, "Refund request submitted for review.")
    elif action == "demo-success" and (request.user.is_staff or (profile and profile.role == StaffProfile.Role.RECEPTIONIST)) and payment.status == Payment.Status.PENDING:
        payment.status = Payment.Status.PAID
        payment.save(update_fields=["status", "updated_at"])
        messages.success(request, "Demo payment marked paid. No real payment gateway was used.")
    elif action == "refund-approve" and request.user.is_staff and payment.status == Payment.Status.REFUND_REQUESTED:
        if payment.provider == "razorpay":
            from django.conf import settings
            import base64, json, urllib.request, urllib.error
            payment_id = payment.provider_reference.split(":")[-1]
            if not (settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET and payment_id.startswith("pay_")):
                messages.error(request, "Cannot refund: Razorpay credentials or captured payment ID are missing.")
                return redirect("staff_dashboard")
            auth = base64.b64encode(f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode()).decode()
            payload = json.dumps({"amount": int(payment.amount * Decimal("100")), "speed": "normal"}).encode()
            req = urllib.request.Request(f"https://api.razorpay.com/v1/payments/{payment_id}/refund", data=payload,
                headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    refund_data = json.loads(response.read().decode())
                payment.status = Payment.Status.REFUNDED
                payment.provider_reference = f"{payment.provider_reference}:refund:{refund_data.get('id','')}"
                payment.save(update_fields=["status", "provider_reference", "updated_at"])
                messages.success(request, "Razorpay accepted the refund request.")
            except (urllib.error.URLError, ValueError):
                messages.error(request, "Razorpay refund request failed. Check the provider dashboard before retrying.")
        else:
            payment.status = Payment.Status.REFUNDED
            payment.save(update_fields=["status", "updated_at"])
            messages.success(request, "Demo refund marked complete. No money was returned by a gateway.")
    else:
        messages.error(request, "That payment action is not permitted.")
    return redirect("dashboard" if is_owner else "staff_dashboard")


@login_required
def razorpay_checkout(request, pk):
    """Create a Razorpay order when configured; no fake success is recorded."""
    import json, base64, urllib.request, urllib.error
    from django.conf import settings
    appointment = get_object_or_404(Appointment.objects.select_related("doctor"), pk=pk, patient=request.user)
    if request.method != "POST":
        return redirect("request_payment", pk=pk)
    if not (settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET):
        messages.warning(request, "Razorpay is not configured. No real charge occurred; use demo mode only.")
        return redirect("request_payment", pk=pk)
    amount_paise = int(appointment.doctor.consultation_fee * Decimal("100"))
    payload = json.dumps({"amount": amount_paise, "currency": "INR", "receipt": f"mc-{appointment.pk}", "notes": {"appointment_id": str(appointment.pk)}}).encode()
    auth = base64.b64encode(f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode()).decode()
    req = urllib.request.Request("https://api.razorpay.com/v1/orders", data=payload, headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
        payment = Payment.objects.create(appointment=appointment, patient=request.user, amount=appointment.doctor.consultation_fee, provider="razorpay", provider_reference=data["id"])
        return render(request, "appointments/razorpay_checkout.html", {"payment": payment, "order": data, "key_id": settings.RAZORPAY_KEY_ID, "appointment": appointment})
    except (urllib.error.URLError, KeyError, ValueError):
        messages.error(request, "Unable to create a payment order. Check Razorpay configuration and try again.")
        return redirect("request_payment", pk=pk)

def razorpay_webhook(request):
    """Verify Razorpay signature before changing payment status."""
    import hmac, hashlib, json
    from django.conf import settings
    from django.http import HttpResponse, JsonResponse
    if request.method != "POST" or not settings.RAZORPAY_WEBHOOK_SECRET:
        return HttpResponse(status=400)
    signature = request.headers.get("X-Razorpay-Signature", "")
    expected = hmac.new(settings.RAZORPAY_WEBHOOK_SECRET.encode(), request.body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return HttpResponse(status=400)
    try:
        event = json.loads(request.body.decode())
        entity = event["payload"]["payment"]["entity"]
        order_id = entity.get("order_id", "")
        payment_id = entity.get("id", "")
        if event.get("event") == "payment.captured":
            Payment.objects.filter(provider="razorpay", provider_reference=order_id, status=Payment.Status.PENDING).update(status=Payment.Status.PAID, provider_reference=f"{order_id}:{payment_id}")
        return JsonResponse({"received": True})
    except (KeyError, ValueError, TypeError):
        return HttpResponse(status=400)
