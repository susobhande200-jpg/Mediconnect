from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=40, default="bi-heart-pulse")
    def __str__(self): return self.name

class DoctorProfile(models.Model):
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="doctor_profile")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="doctors")
    qualification = models.CharField(max_length=180)
    experience_years = models.PositiveSmallIntegerField(default=1)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=300)
    bio = models.TextField(blank=True)
    languages = models.CharField(max_length=160, default="English, Bengali")
    is_approved = models.BooleanField(default=False)
    online_consultation = models.BooleanField(default=True)
    def __str__(self): return f"Dr. {self.user.get_full_name() or self.user.username}"
