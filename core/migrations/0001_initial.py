import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="Department", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=100, unique=True)),
            ("description", models.TextField(blank=True)),
            ("icon", models.CharField(default="bi-heart-pulse", max_length=40)),
        ]),
        migrations.CreateModel(name="DoctorProfile", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("qualification", models.CharField(max_length=180)),
            ("experience_years", models.PositiveSmallIntegerField(default=1)),
            ("consultation_fee", models.DecimalField(decimal_places=2, default=300, max_digits=8)),
            ("bio", models.TextField(blank=True)),
            ("languages", models.CharField(default="English, Bengali", max_length=160)),
            ("is_approved", models.BooleanField(default=False)),
            ("online_consultation", models.BooleanField(default=True)),
            ("department", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="doctors", to="core.department")),
            ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="doctor_profile", to=settings.AUTH_USER_MODEL)),
        ]),
    ]
