from django import forms
from django.utils import timezone
from .models import Appointment, ConsultationNote, Prescription, PrescriptionItem, ChatMessage

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ("doctor", "appointment_date", "start_time", "end_time", "appointment_type", "reason")
        widgets = {"appointment_date": forms.DateInput(attrs={"type":"date","class":"form-control"}),
                   "start_time": forms.TimeInput(attrs={"type":"time","class":"form-control"}),
                   "end_time": forms.TimeInput(attrs={"type":"time","class":"form-control"}),
                   "reason": forms.Textarea(attrs={"rows":3,"class":"form-control"}),
                   "doctor": forms.Select(attrs={"class":"form-select"}),
                   "appointment_type": forms.Select(attrs={"class":"form-select"})}
    def __init__(self, *args, **kwargs):
        from core.models import DoctorProfile
        super().__init__(*args, **kwargs)
        self.fields["doctor"].queryset = DoctorProfile.objects.filter(is_approved=True).select_related("user","department")
        self.fields["doctor"].widget.attrs["class"] = "form-select"
    def clean(self):
        cleaned = super().clean()
        date, start, end, doctor = cleaned.get("appointment_date"), cleaned.get("start_time"), cleaned.get("end_time"), cleaned.get("doctor")
        if date and date < timezone.localdate(): self.add_error("appointment_date", "Please choose today or a future date.")
        if start and end and end <= start: self.add_error("end_time", "End time must be after start time.")
        if doctor and date and start and end and end > start:
            qs = Appointment.objects.filter(doctor=doctor, appointment_date=date, status__in=[Appointment.Status.PENDING,Appointment.Status.CONFIRMED], start_time__lt=end, end_time__gt=start)
            if self.instance.pk: qs = qs.exclude(pk=self.instance.pk)
            if qs.exists(): self.add_error("start_time", "That time overlaps an existing booking.")
        return cleaned

class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ("body", "shared_meet_url")
        widgets = {"body": forms.Textarea(attrs={"rows":2,"class":"form-control","placeholder":"Write a message to the patient or doctor…"}),
                   "shared_meet_url": forms.URLInput(attrs={"class":"form-control","placeholder":"Optional Google Meet link (https://meet.google.com/…)"} )}
    def clean_shared_meet_url(self):
        url = self.cleaned_data.get("shared_meet_url", "")
        if url and "meet.google.com/" not in url:
            raise forms.ValidationError("Please enter a valid Google Meet URL containing meet.google.com/.")
        return url

class ConsultationNoteForm(forms.ModelForm):
    class Meta:
        model = ConsultationNote
        fields = ("symptoms","examination","assessment","treatment_plan","follow_up_date","finalized")
        widgets = {k: forms.Textarea(attrs={"rows":3,"class":"form-control"}) for k in ("symptoms","examination","assessment","treatment_plan")}
        widgets["follow_up_date"] = forms.DateInput(attrs={"type":"date","class":"form-control"})

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ("instructions",)
        widgets = {"instructions": forms.Textarea(attrs={"rows":2,"class":"form-control"})}

class PrescriptionItemForm(forms.ModelForm):
    class Meta:
        model = PrescriptionItem
        fields = ("medication_name","dosage","route","frequency","duration","notes")
        widgets = {k: forms.TextInput(attrs={"class":"form-control"}) for k in ("medication_name","dosage","route","frequency","duration","notes")}
