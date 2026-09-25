# Telemedical Consultation Platform

A secure web-based telemedicine platform for remote consultations (video/audio/chat), appointment booking, e-prescriptions, medical records, and role-based access.

## Tech Stack

- Django (latest stable)
- PostgreSQL (production) / SQLite (development)
- Bootstrap 5
- Python 3.10+

## Quick Start

1. **Clone and create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment**
   ```bash
   copy .env.example .env
   # Edit .env: set SECRET_KEY and optionally DEBUG, ALLOWED_HOSTS
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run server**
   ```bash
   python manage.py runserver
   ```

## Project Structure

See `PROJECT_STRUCTURE.md` for the full folder layout.

## Roles

- **Patient**: Register, book appointments, view prescriptions, messaging, consultation history.
- **Healthcare Provider**: Register (pending approval), manage availability, accept/reject appointments, conduct consultations, create e-prescriptions.
- **Administrator**: Approve providers, manage users, analytics dashboard, audit logs.

## License

Proprietary — Group 5 Appoint.
# MEDICAL
