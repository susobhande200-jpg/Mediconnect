from django.contrib import admin
from .models import Appointment, MedicalRecord, ConsultationNote, Prescription, PrescriptionItem, Payment, ChatMessage

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("reference", "patient", "doctor", "appointment_date", "start_time", "status", "appointment_type")
    list_filter = ("status", "appointment_type", "appointment_date", "doctor__department")
    search_fields = ("patient__username", "patient__email", "doctor__user__username", "doctor__user__first_name", "reference")
    readonly_fields = ("reference", "created_at")
    actions = ["confirm_appointments", "complete_appointments"]
    @admin.action(description="Mark selected appointments confirmed")
    def confirm_appointments(self, request, queryset):
        queryset.filter(status=Appointment.Status.PENDING).update(status=Appointment.Status.CONFIRMED)
    @admin.action(description="Mark selected appointments completed")
    def complete_appointments(self, request, queryset):
        queryset.filter(status=Appointment.Status.CONFIRMED).update(status=Appointment.Status.COMPLETED)

class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 0
@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "doctor", "appointment", "created_at")
    list_filter = ("created_at",)
    search_fields = ("patient__username", "doctor__user__username", "appointment__reference")
    inlines = [PrescriptionItemInline]
@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ("title", "patient", "doctor", "record_type", "created_at")
    search_fields = ("patient__username", "title")
@admin.register(ConsultationNote)
class ConsultationNoteAdmin(admin.ModelAdmin):
    list_display = ("appointment", "author", "finalized", "updated_at")
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "appointment", "amount", "status", "provider", "created_at")
    list_filter = ("status", "provider", "created_at")
    search_fields = ("patient__username", "appointment__reference", "provider_reference")
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("appointment", "sender", "created_at")
    search_fields = ("body", "sender__username")
