# MediConnect — Doctor Appointment & Clinic Management System

**College project starter** built with Django 5.2, Bootstrap 5, SQLite/PostgreSQL, and a responsive healthcare UI.

> Important scope note: this is a working foundation for a college demonstration, not a certified production healthcare platform. It implements public doctor discovery, patient registration/login, appointment requests, patient dashboard, cancellation, Django admin management, and Google Meet URL storage/display. It does **not** yet implement every item in the original long master prompt (for example, real payment gateway transactions, complete medical records, SMS/email verification, all staff dashboards, and a fully automated Google Calendar/Meet OAuth flow). Do not use real patient medical data.

## Features implemented
- Responsive MediConnect brand and landing page.
- Doctor directory with name/department search and doctor profile.
- Patient account registration and Django authentication.
- Patient dashboard and appointment history.
- Appointment booking, date/time validation, overlap checks, cancellation.
- Admin management for departments, doctors, appointments, and patient profiles.
- Appointment states: pending, confirmed, completed, cancelled, rejected.
- Online consultation type and protected-in-dashboard Meet link display when a link has been added by an authorized admin.
- SQLite locally, PostgreSQL through `DATABASE_URL`.
- WhiteNoise static files, health endpoint, Render blueprint, environment configuration.

## Implemented in this expanded version
- Separate doctor and receptionist dashboards with server-side role checks and admin approval.
- Doctor appointment confirmation/rejection/completion actions.
- Doctor-entered consultation notes and prescription with medication item fields.
- Patient-visible authorized medical-record and prescription summaries.
- Patient/doctor appointment chat with optional Google Meet link sharing; link validation requires `meet.google.com`.
- Email verification link generation (SMTP is required for actual delivery; local default prints email to the terminal).
- Appointment reminder management command; schedule it daily on the host to automate delivery.
- Demo payment records and optional Razorpay order creation with signed webhook validation for captured payment events.
- Refund request tracking and admin-side demo refund workflow.

## Still limited / not production complete
- Automatic Google Meet link generation through Google Calendar API is not implemented. Doctor and patient can chat and share a Google Meet URL manually.
- Refund status is tracked in the demo workflow, but automated live Razorpay refund API execution is not implemented.
- The payment UI/webhook must be configured and verified with Razorpay test credentials before any real use. Do not accept real payments until tested end-to-end.
- Email verification is a signed link, not OTP; SMTP delivery must be configured.
- Reminder command must be scheduled externally and does not itself run in the background.
- PDF receipts/prescriptions, full lab records, analytics charts, waiting-room queue, review moderation and complete audit history remain future tasks.
- Email verification and real SMTP delivery (password-reset view is present; configure SMTP).
- Actual payment gateway, refund processing, PDF receipts/prescriptions, full clinical records, laboratory module, reviews, support tickets, analytics charts, calendar UI, complete role-based doctor/receptionist dashboards, waitlists, background reminders.
- Full automated test coverage of the entire original specification.

## Windows installation (PowerShell)
Use Python 3.12 or 3.13 for easiest compatibility with common dependencies.

```powershell
cd MediConnect
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py makemigrations core accounts appointments
python manage.py migrate
python manage.py check
python manage.py test
python manage.py createsuperuser
python manage.py runserver
```
Open http://127.0.0.1:8000/

If PowerShell blocks activation, use Command Prompt:
```bat
.venv\Scripts\activate.bat
```

## Add demo data
After migrations, run:
```powershell
python manage.py seed_demo
```
This creates example departments, doctors, and a demo patient. Demo passwords are for local testing only; change them immediately and never deploy demo accounts with known passwords.

Admin URL: http://127.0.0.1:8000/admin/

## Render deployment
- Push the project to a GitHub repository.
- Create a Render Web Service from the repository, or use the included `render.yaml` blueprint.
- Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput`
- Start command: `gunicorn config.wsgi:application`
- Set `DJANGO_SECRET_KEY` to a long random secret and `DJANGO_DEBUG=False`.
- Set `DJANGO_ALLOWED_HOSTS` to your Render hostname (the settings also allow `.onrender.com` in production).
- Use a persistent PostgreSQL database and configure `DATABASE_URL`. Do not rely on local SQLite or uploaded media being persistent on an ephemeral web service.
- Create the admin account using a secure one-off shell/command supported by your host, or locally and migrate appropriately. Never hardcode admin passwords in source code or build commands.
- After deployment, visit `/health/`.

## Google Meet link sharing
The current chat lets an authorized appointment participant send a message and optionally share a `https://meet.google.com/...` link. The recipient sees a Join Google Meet link inside that appointment's private chat. The system does not generate a Meet link automatically. To create real links automatically later, configure a Google Cloud project, enable Google Calendar API, configure OAuth consent and authorized redirect URI, and request the least-privilege calendar scopes. The server should create a Calendar event with conference data, save the event ID and confirmed Meet URL to the appointment, and handle pending/failed conference creation. Never expose OAuth tokens. This starter does not generate links automatically; the admin can paste a link into the appointment's `meet_url` field.

## Security checklist before any real-world use
- Set `DEBUG=False` and a strong environment-only secret.
- Configure exact allowed hosts and HTTPS/CSRF settings.
- Configure SMTP and password-reset email delivery.
- Remove demo users and sample data.
- Add tests and review role/object permissions.
- Use private file storage for sensitive uploads.
- Integrate real payment gateway webhooks securely before accepting payments.
- Obtain a professional privacy/security and regulatory review before handling real patient data.

## Email reminders
Run `python manage.py send_appointment_reminders` to send reminders for confirmed appointments today/tomorrow. To automate, configure your hosting provider's scheduled job to run this command daily. Without a scheduler, reminders do not run automatically.

## Razorpay test setup
Set `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and `RAZORPAY_WEBHOOK_SECRET` in environment variables. Configure a Razorpay webhook to `https://YOUR-DOMAIN/appointments/razorpay/webhook/` and subscribe to `payment.captured`. Use test keys first. Never mark a payment paid based on the browser callback alone; only a verified webhook changes the status. Test order creation and webhook reconciliation before using live credentials.
