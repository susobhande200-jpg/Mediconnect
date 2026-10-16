from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Department, DoctorProfile

def home(request):
    departments = Department.objects.all()[:6]
    doctors = DoctorProfile.objects.filter(is_approved=True).select_related("user", "department")[:4]
    return render(request, "core/home.html", {"departments": departments, "doctors": doctors})

def doctor_list(request):
    doctors = DoctorProfile.objects.filter(is_approved=True).select_related("user", "department")
    q = request.GET.get("q", "").strip()
    dept = request.GET.get("department", "").strip()
    if q:
        doctors = doctors.filter(Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) | Q(department__name__icontains=q))
    if dept:
        doctors = doctors.filter(department_id=dept)
    return render(request, "core/doctors.html", {"doctors": doctors, "departments": Department.objects.all(), "q": q, "selected_department": dept})

def doctor_detail(request, pk):
    doctor = get_object_or_404(DoctorProfile.objects.select_related("user", "department"), pk=pk, is_approved=True)
    return render(request, "core/doctor_detail.html", {"doctor": doctor})
