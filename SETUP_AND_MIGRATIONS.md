# Setup and migration instructions

## Prerequisites

- Python 3.10+
- (Production) PostgreSQL server

## 1. Virtual environment and dependencies

```powershell
# Windows
cd "Group 5 Appoint"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
# Linux/macOS
cd "Group 5 Appoint"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Environment variables

```powershell
copy .env.example .env
# Edit .env and set at least:
#   SECRET_KEY=<a long random string>
#   DEBUG=True for development
#   ALLOWED_HOSTS=localhost,127.0.0.1
```

For production, set `DEBUG=False`, a strong `SECRET_KEY`, and `ALLOWED_HOSTS` to your domain. Use `DATABASE_URL` for PostgreSQL (e.g. `postgres://user:password@localhost:5432/telemedicine_db`).

## 3. Migrations

```bash
# Create migrations (already done if you pulled the repo with migrations)
python manage.py makemigrations accounts audit_logs appointments consultations messaging prescriptions medical_records

# Apply migrations
python manage.py migrate
```

## 4. Superuser and first admin

```bash
python manage.py createsuperuser
# Enter username, email, password.
# Then in Django admin (or shell), set the user's role to ADMIN if you use the custom User model.
```

To set role via shell:

```bash
python manage.py shell
>>> from accounts.models import CustomUser
>>> u = CustomUser.objects.get(username='your_admin_username')
>>> u.role = CustomUser.Role.ADMIN
>>> u.save()
```

## 5. Run development server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/

## 6. Optional: static files (production)

```bash
python manage.py collectstatic --noinput
```

## Switching to PostgreSQL

1. Install PostgreSQL and create a database.
2. Set in `.env`:
   ```
   DATABASE_URL=postgres://USER:PASSWORD@HOST:5432/DATABASE_NAME
   ```
3. Use production settings:
   ```
   set DJANGO_SETTINGS_MODULE=config.settings.production
   ```
4. Run `python manage.py migrate` again (with the same migrations; DB is empty on new DB).

## Summary of apps and models

| App            | Main models                                      |
|----------------|--------------------------------------------------|
| accounts       | CustomUser, PatientProfile, ProviderProfile     |
| audit_logs     | AuditLog                                         |
| appointments   | Appointment, ProviderAvailability                |
| consultations  | Consultation                                    |
| prescriptions  | Prescription, PrescriptionItem                  |
| medical_records| MedicalRecord                                   |
| messaging      | Conversation, Message                           |
| dashboard      | (no models – views only)                        |
