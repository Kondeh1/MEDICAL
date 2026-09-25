# Telemedical Consultation Platform — Project Structure

```
Group 5 Appoint/
│
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── PROJECT_STRUCTURE.md
│
├── config/                          # Project configuration package
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                  # Shared settings
│   │   ├── development.py           # SQLite, DEBUG=True
│   │   └── production.py            # PostgreSQL, DEBUG=False
│   ├── urls.py                      # Root URLconf
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/                        # Custom User & roles
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py                    # CustomUser
│   ├── views.py
│   ├── urls.py
│   ├── mixins.py                    # Role-based access mixins
│   ├── signals.py
│   └── templates/
│       └── accounts/
│           ├── login.html
│           ├── register.html
│           ├── register_patient.html
│           ├── register_provider.html
│           ├── profile.html
│           ├── profile_edit.html
│           └── password_change.html
│
├── appointments/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py                    # Appointment
│   ├── views.py
│   ├── urls.py
│   └── templates/
│       └── appointments/
│           ├── list.html
│           ├── detail.html
│           ├── book.html
│           ├── provider_schedule.html
│           └── accept_reject.html
│
├── consultations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py                    # Consultation
│   ├── views.py
│   ├── urls.py
│   └── templates/
│       └── consultations/
│           ├── list.html
│           ├── detail.html
│           └── room.html             # Chat-based consultation room
│
├── prescriptions/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py                    # Prescription, PrescriptionItem
│   ├── views.py
│   ├── urls.py
│   └── templates/
│       └── prescriptions/
│           ├── list.html
│           ├── detail.html
│           └── create.html
│
├── medical_records/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py                    # MedicalRecord
│   ├── views.py
│   ├── urls.py
│   └── templates/
│       └── medical_records/
│           ├── list.html
│           ├── detail.html
│           └── create.html
│
├── messaging/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py                    # Message, Conversation
│   ├── views.py
│   ├── urls.py
│   └── templates/
│       └── messaging/
│           ├── inbox.html
│           └── thread.html
│
├── dashboard/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── views.py                     # Role-specific dashboards + admin analytics
│   ├── urls.py
│   └── templates/
│       └── dashboard/
│           ├── base_dashboard.html
│           ├── patient_dashboard.html
│           ├── provider_dashboard.html
│           └── admin_dashboard.html
│
├── audit_logs/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py                    # AuditLog
│   ├── utils.py                     # log_action helper
│   ├── views.py                     # Admin-only list/filter
│   ├── urls.py
│   └── templates/
│       └── audit_logs/
│           └── list.html
│
├── templates/                       # Global templates
│   ├── base.html
│   ├── 403.html
│   ├── 404.html
│   ├── 500.html
│   └── registration/
│       └── (if any shared auth templates)
│
└── static/
    ├── css/
    │   └── styles.css
    ├── js/
    │   └── main.js
    └── img/
        └── (optional assets)
```

## Module summary

| Module         | Purpose |
|----------------|---------|
| **config**     | Django project settings (base/dev/prod), root URLs, WSGI/ASGI |
| **accounts**   | CustomUser (Patient/Provider/Admin), profiles, auth, mixins, signals |
| **appointments** | Booking, provider schedule, accept/reject |
| **consultations** | Consultation model, chat-based consultation room |
| **prescriptions** | E-prescriptions and items |
| **medical_records** | Medical records linked to patients |
| **messaging**  | Secure messaging (Conversation, Message) |
| **dashboard**  | Patient/Provider/Admin dashboards + admin analytics |
| **audit_logs** | AuditLog model, log_action utility, admin views |

Next step: generating code file-by-file, starting with **config** and **manage.py** / **requirements.txt** / **.env.example** / **.gitignore**.
