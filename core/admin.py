from django.contrib import admin
from .models import Department, DoctorProfile
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    search_fields = ("name",)
@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "experience_years", "consultation_fee", "is_approved")
    list_filter = ("department", "is_approved")
    search_fields = ("user__username", "user__first_name", "user__last_name")
