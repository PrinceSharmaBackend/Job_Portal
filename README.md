# 🧑‍💼 Job Portal Management System

A production-ready REST API for a Job Portal built with **Django**, **Django REST Framework**, **PostgreSQL**, and **JWT Authentication**. Containerized with Docker.

---

## 🚀 Tech Stack

| Layer        | Technology                        |
|--------------|-----------------------------------|
| Backend      | Django 5.0, Django REST Framework |
| Auth         | JWT (SimpleJWT)                   |
| Database     | PostgreSQL 16                     |
| Filtering    | django-filter                     |
| API Docs     | drf-spectacular (Swagger/ReDoc)   |
| Container    | Docker + docker-compose           |

---

## 📁 Project Structure

```
job_portal/
├── apps/
│   ├── accounts/       # Custom User model, Auth (register/login/logout)
│   └── jobs/           # Jobs, Applications, Saved Jobs
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## ⚙️ Setup — With Docker (Recommended)

```bash
# 1. Clone the repo
git clone <repo-url>
cd job_portal

# 2. Copy env file and fill in values
cp .env.example .env

# 3. Build and run
docker-compose up --build

# 4. Create a superuser (in a new terminal)
docker-compose exec web python manage.py createsuperuser
```

API will be live at **http://localhost:8000**

---

## ⚙️ Setup — Without Docker (Local)

```bash
# 1. Create virtualenv
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy env and set DB_HOST=localhost
cp .env.example .env

# 4. Run migrations
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser

# 6. Start server
python manage.py runserver
```

---

## 📌 API Endpoints

### Auth
| Method | Endpoint                        | Description              | Access     |
|--------|---------------------------------|--------------------------|------------|
| POST   | `/api/v1/auth/register/`        | Register new account     | Public     |
| POST   | `/api/v1/auth/login/`           | Login → get JWT tokens   | Public     |
| POST   | `/api/v1/auth/logout/`          | Logout (blacklist token) | Auth       |
| POST   | `/api/v1/auth/token/refresh/`   | Refresh access token     | Public     |
| GET    | `/api/v1/auth/me/`              | Get my profile           | Auth       |
| PUT    | `/api/v1/auth/me/`              | Update my profile        | Auth       |
| POST   | `/api/v1/auth/change-password/` | Change password          | Auth       |

### Jobs (Public)
| Method | Endpoint                  | Description                       |
|--------|---------------------------|-----------------------------------|
| GET    | `/api/v1/jobs/`           | List all active jobs (filter, search, paginate) |
| GET    | `/api/v1/jobs/<id>/`      | Job detail (increments view count) |
| GET    | `/api/v1/jobs/categories/`| List all categories               |

### Employer
| Method | Endpoint                                          | Description                    |
|--------|---------------------------------------------------|--------------------------------|
| GET    | `/api/v1/jobs/employer/jobs/`                     | My posted jobs                 |
| POST   | `/api/v1/jobs/employer/jobs/`                     | Post a new job                 |
| GET    | `/api/v1/jobs/employer/jobs/<id>/`                | Job detail                     |
| PUT    | `/api/v1/jobs/employer/jobs/<id>/`                | Update job                     |
| DELETE | `/api/v1/jobs/employer/jobs/<id>/`                | Delete job                     |
| GET    | `/api/v1/jobs/employer/jobs/<id>/applications/`   | View all applications for job  |
| PATCH  | `/api/v1/jobs/employer/applications/<id>/status/` | Update application status      |
| GET    | `/api/v1/jobs/employer/dashboard/`                | Stats dashboard                |

### Job Seeker
| Method | Endpoint                                      | Description              |
|--------|-----------------------------------------------|--------------------------|
| POST   | `/api/v1/jobs/apply/`                         | Apply for a job          |
| GET    | `/api/v1/jobs/my-applications/`               | View all my applications |
| DELETE | `/api/v1/jobs/my-applications/<id>/withdraw/` | Withdraw application     |
| GET    | `/api/v1/jobs/saved/`                         | View saved jobs          |
| POST   | `/api/v1/jobs/<id>/save/`                     | Save / unsave a job      |
| GET    | `/api/v1/jobs/dashboard/`                     | My stats dashboard       |

---

## 🔐 Authentication

All protected routes require a JWT access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

---

## 🔍 Search & Filter

```
GET /api/v1/jobs/?search=python
GET /api/v1/jobs/?job_type=remote&experience_level=entry
GET /api/v1/jobs/?salary_min=30000&salary_max=80000
GET /api/v1/jobs/?location=Mumbai&is_remote=true
GET /api/v1/jobs/?ordering=-created_at
```

---

## 📖 API Documentation

Interactive docs available after starting the server:

- **Swagger UI** → http://localhost:8000/api/docs/
- **ReDoc**      → http://localhost:8000/api/redoc/
- **Admin Panel** → http://localhost:8000/admin/

---

## 👤 User Roles

| Role        | Capabilities                                             |
|-------------|----------------------------------------------------------|
| Job Seeker  | Browse jobs, apply, save, track application status       |
| Employer    | Post jobs, manage applications, update application status |
| Admin       | Full access via Django Admin                             |

---

## 🧪 Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=apps --cov-report=term-missing

# Run specific app tests
pytest apps/accounts/tests/
pytest apps/jobs/tests/
```

---

## 🌱 Load Seed Data

```bash
# Load categories
python manage.py loaddata fixtures/categories.json
```

---

## ⏰ Job Expiry (Cron Job)

Auto-close jobs past their deadline:

```bash
python manage.py close_expired_jobs
```

Add to crontab to run daily:
```
0 0 * * * /path/to/venv/bin/python /path/to/manage.py close_expired_jobs
```

---

## 📧 Email Notifications

In development, emails print to the terminal (console backend).
For production, set SMTP variables in `.env`:

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

Emails sent automatically:
- ✅ Applicant receives confirmation when they apply
- ✅ Employer notified when someone applies to their job
- ✅ Applicant notified when status changes (shortlisted / rejected / hired)

---

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","first_name":"Prince","last_name":"Dev","role":"job_seeker","password":"Test@1234","confirm_password":"Test@1234"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test@1234"}'
```

---

## 🏗️ Built for QSkill Internship | Backend Development Track
