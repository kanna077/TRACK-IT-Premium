# TRACK-IT — Smart Campus Lost \& Found with AI

TRACK-IT is a full-stack, submission-ready campus lost-and-found platform built with **Next.js + TypeScript**, **Django REST Framework**, **PostgreSQL/pgvector**, **Redis**, **Celery-ready jobs**, and optional **WebSocket notifications**.

The premium interface supports verified registration, lost/found reporting, explainable AI-assisted matching, private ownership claims, secure claim messaging, faculty/admin review, QR + OTP handover, reports, notifications and an informational assistant.

## Core features

* Role-based users: Campus User, Faculty, External Finder and Administrator
* Email registration OTP with expiry, resend and attempt limits
* College-domain restriction for campus users (`@gcet.edu.in`)
* Lost/found item reports with image upload and validation
* Search and filters by type, status, category, text and location
* Explainable AI-assisted match ranking
* Private ownership evidence and staff-controlled approval/rejection
* One approved claim per item
* Single-use, time-limited QR token + 6-digit handover OTP
* Secure claim messages
* REST notifications plus optional WebSocket delivery
* PDF and Excel-compatible XLSX exports
* Dashboard metrics and staff analytics API
* Informational FAQ assistant
* PostgreSQL pgvector extension initialization
* Docker deployment for database, Redis, backend, worker and frontend
* Automated backend, TypeScript and lint checks

## Important safety rule

AI match scores are **suggestions only**. They never establish ownership. Ownership is decided through private evidence, authorized review and secure handover verification.

## Project structure

```text
track-it/
├── backend/
│   ├── apps/
│   │   ├── accounts/
│   │   ├── items/
│   │   ├── claims/
│   │   ├── qr\_tracking/
│   │   ├── notifications/
│   │   ├── messaging/
│   │   └── chatbot/
│   ├── config/
│   ├── Dockerfile
│   └── manage.py
├── frontend/
│   ├── src/app/
│   ├── src/lib/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── setup.ps1
├── run-backend.ps1
├── run-frontend.ps1
└── test-project.ps1
```

## Fast Windows setup

### 1\. Extract the ZIP

Extract the project to:

```text
D:\\track-it-premium
```

Open PowerShell inside that folder.

### 2\. Create the local environment

```powershell
Copy-Item .env.example .env
```

Open `.env` and set a strong PostgreSQL password. To send real OTP emails through Gmail, add the sender Gmail address and its Google App Password.

Never commit or share `.env`.

### 3\. Automated setup

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\\setup.ps1
```

This creates the virtual environment, installs packages, starts PostgreSQL and Redis, runs migrations, creates demo data and installs the frontend.

### 4\. Start both servers

Backend terminal:

```powershell
.\\run-backend.ps1
```

Frontend terminal:

```powershell
.\\run-frontend.ps1
```

Open:

* Frontend: `http://localhost:3000`
* Django admin: `http://127.0.0.1:8000/admin/`
* API health: `http://127.0.0.1:8000/api/v1/health/`

## Manual setup

### Backend

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Copy-Item .env.example .env
docker compose up -d db redis

python backend\\manage.py migrate
python backend\\manage.py createsuperuser
python backend\\manage.py runserver
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Demo data

Create a complete demonstration dataset:

```powershell
python backend\\manage.py seed\_demo
```



Replace the whole section with:



```text

Demo accounts:



Create demonstration accounts locally with:



```powershell

python backend\\manage.py seed\_demo```

Change these passwords before public deployment.

## Real Gmail OTP configuration

Add this to `.env`:

```env
EMAIL\_HOST=smtp.gmail.com
EMAIL\_PORT=587
EMAIL\_USE\_TLS=True
EMAIL\_HOST\_USER=your-sender@gmail.com
EMAIL\_HOST\_PASSWORD=your-google-app-password-without-spaces
DEFAULT\_FROM\_EMAIL=TRACK-IT <your-sender@gmail.com>
```

The sender Gmail is used only to deliver mail. Every OTP is sent dynamically to the email entered by the registering user.

When `EMAIL\_HOST\_USER` is empty, Django uses the console email backend and prints the OTP email in the backend terminal. This is useful for local testing.

## Database modes

Production/Docker:

```env
DB\_ENGINE=postgres
```

Quick offline demonstration:

```env
DB\_ENGINE=sqlite
```

PostgreSQL remains the recommended deployment database. The project enables the `vector` extension when migrations run against PostgreSQL.

## Recommended demonstration flow

1. Sign in as `student1` and open the LOST wallet report.
2. Run AI Matches and view the ranked FOUND wallet suggestion.
3. Sign in as another verified user and submit an ownership claim.
4. Sign in as `admin1`, review and approve the claim.
5. Open the generated QR token and OTP.
6. Complete the handover as administrator.
7. Confirm that the dashboard Returned count increases.
8. Try using the same token again; it must be rejected as already used.
9. Download PDF and Excel reports.
10. Demonstrate notifications, messages and the assistant.

## Tests

Run:

```powershell
.\\test-project.ps1
```

Individual commands:

```powershell
$env:DB\_ENGINE="sqlite"
python backend\\manage.py test
python backend\\manage.py makemigrations --check --dry-run

cd frontend
npm run typecheck
npm run lint
npm run build
```

## Deployment

The included Docker Compose stack contains:

* PostgreSQL with pgvector
* Redis
* Django/ASGI backend
* Celery worker
* Next.js standalone frontend

For a public deployment:

1. Set `DEBUG=False`.
2. Generate a strong `DJANGO\_SECRET\_KEY`.
3. Configure real domains in `ALLOWED\_HOSTS`, `FRONTEND\_URL` and `CORS\_ALLOWED\_ORIGINS`.
4. Use HTTPS and secure reverse-proxy headers.
5. Store secrets in the hosting platform, not in source control.
6. Configure durable media storage.
7. Create a restricted database user.
8. Replace all demo passwords.

## Browser support

Designed for current versions of:

* Google Chrome
* Microsoft Edge
* Firefox
* Modern mobile browsers

