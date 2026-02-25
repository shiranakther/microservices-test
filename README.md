# Microservices with FastAPI

A fully working microservices architecture built with **Python + FastAPI**, featuring a central API Gateway, two independent microservices, JWT authentication, request logging, and environment-based configuration.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Project Structure](#2-project-structure)
3. [Technology Stack](#3-technology-stack)
4. [Environment Configuration](#4-environment-configuration)
5. [Setup & Installation](#5-setup--installation)
6. [Running the Services](#6-running-the-services)
7. [API Reference](#7-api-reference)
   - [API Gateway (Port 8000)](#api-gateway-port-8000)
   - [Student Microservice (Port 8001)](#student-microservice-port-8001)
   - [Course Microservice (Port 8002)](#course-microservice-port-8002)
8. [Authentication Flow](#8-authentication-flow)
9. [Request Logging](#9-request-logging)
10. [Error Handling](#10-error-handling)
11. [Testing with Swagger UI](#11-testing-with-swagger-ui)
12. [Activities Summary](#12-activities-summary)

---

## 1. Architecture Overview

```
                        ┌────────────────────────────────┐
                        │          CLIENT                │
                        │  (Browser / Postman / curl)    │
                        └──────────────┬─────────────────┘
                                       │  HTTP Requests
                                       ▼
                        ┌────────────────────────────────┐
                        │        API GATEWAY             │
                        │        Port 8000               │
                        │                                │
                        │  ✔ JWT Authentication          │
                        │  ✔ Request/Response Logging    │
                        │  ✔ Global Error Handling       │
                        │  ✔ Request Forwarding (Proxy)  │
                        └───────┬────────────┬───────────┘
                                │            │
               /gateway/students│            │/gateway/courses
                                │            │
               ┌────────────────▼──┐   ┌────▼──────────────────┐
               │ Student Service   │   │  Course Service        │
               │ Port 8001         │   │  Port 8002             │
               │                   │   │                        │
               │ GET  /api/students│   │ GET  /api/courses      │
               │ POST /api/students│   │ POST /api/courses      │
               │ PUT  /api/students│   │ PUT  /api/courses      │
               │ DELETE ...        │   │ DELETE ...             │
               │                   │   │                        │
               │ [In-Memory Store] │   │ [In-Memory Store]      │
               └───────────────────┘   └────────────────────────┘
```

### The Restaurant Analogy

| Concept      | In This Project          |
| ------------ | ------------------------ |
| **Customer** | Client (you/browser)     |
| **Waiter**   | API Gateway (port 8000)  |
| **Kitchen**  | Student / Course Service |

The customer never walks into the kitchen — they talk to the waiter. The waiter takes the order (request) and delegates it to the correct kitchen station (microservice), then brings back the food (response).

---

## 2. Project Structure

```
microservices-fastapi/
│
├── .env                        ← 🔒 Your secrets (NEVER commit this)
├── .env.example                ← ✅ Template — safe to commit
├── .gitignore                  ← Excludes .env, venv, __pycache__
├── requirements.txt            ← All Python dependencies
│
├── student-service/            ← Microservice 1 (Port 8001)
│   ├── main.py                 ← FastAPI app + REST endpoints
│   ├── models.py               ← Pydantic data models
│   ├── service.py              ← Business logic layer
│   └── data_service.py        ← In-memory data store (mock DB)
│
├── course-service/             ← Microservice 2 (Port 8002)
│   ├── main.py                 ← FastAPI app + REST endpoints
│   ├── models.py               ← Pydantic data models
│   ├── service.py              ← Business logic layer
│   └── data_service.py        ← In-memory data store (mock DB)
│
├── gateway/
│   └── main.py                 ← API Gateway (Port 8000)
│                                    JWT auth, logging, proxy routing
│
└── venv/                       ← Python virtual environment
```

### Layer Architecture (Per Microservice)

```
HTTP Request
     │
     ▼
 main.py          ← Controller layer   (routes, HTTP status codes)
     │
     ▼
 service.py       ← Business logic     (validation, transformation)
     │
     ▼
 data_service.py  ← Data access layer  (CRUD on in-memory list / future DB)
     │
     ▼
 models.py        ← Data models        (Pydantic schemas)
```

---

## 3. Technology Stack

| Component        | Technology             | Version |
| ---------------- | ---------------------- | ------- |
| Web framework    | FastAPI                | 0.104.1 |
| ASGI server      | Uvicorn                | 0.24.0  |
| Data validation  | Pydantic               | 2.5.0   |
| HTTP client      | HTTPX                  | 0.25.1  |
| JWT tokens       | python-jose            | 3.3.0   |
| Password hashing | passlib (sha256_crypt) | 1.7.4   |
| Env management   | python-dotenv          | 1.0.0   |
| Form parsing     | python-multipart       | 0.0.6   |
| Language         | Python                 | 3.8+    |

---

## 4. Environment Configuration

All secrets and configuration values are stored in a single `.env` file at the project root. **Never commit `.env` to version control.**

### `.env` File

```ini
# JWT Authentication
SECRET_KEY=super-secret-key-change-me-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Downstream Microservice URLs
STUDENT_SERVICE_URL=http://localhost:8001
COURSE_SERVICE_URL=http://localhost:8002

# Demo Gateway Users
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secret
VIEWER_USERNAME=student
VIEWER_PASSWORD=pass123
```

### Variable Reference

| Variable                      | Used In | Purpose                                |
| ----------------------------- | ------- | -------------------------------------- |
| `SECRET_KEY`                  | Gateway | Signs and verifies JWT tokens          |
| `ALGORITHM`                   | Gateway | JWT signing algorithm (default: HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Gateway | How long tokens are valid              |
| `STUDENT_SERVICE_URL`         | Gateway | Base URL of the Student microservice   |
| `COURSE_SERVICE_URL`          | Gateway | Base URL of the Course microservice    |
| `ADMIN_USERNAME`              | Gateway | Username for the admin demo user       |
| `ADMIN_PASSWORD`              | Gateway | Password for the admin demo user       |
| `VIEWER_USERNAME`             | Gateway | Username for the viewer demo user      |
| `VIEWER_PASSWORD`             | Gateway | Password for the viewer demo user      |

### How It's Loaded in Code

```python
from dotenv import find_dotenv, load_dotenv
import os

load_dotenv(find_dotenv())   # Walks up from service dir → finds project root .env

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-only-key")
```

`find_dotenv()` automatically walks **up** the directory tree, so all three services (running from their own subdirectories) share the **same single `.env`** at the project root.

---

## 5. Setup & Installation

### Prerequisites

- Python 3.8 or higher
- pip

Check your Python version:

```bash
python --version
```

### Step-by-Step Setup

**1. Clone / navigate to the project folder:**

```bash
cd microservices-fastapi
```

**2. Create and activate the virtual environment:**

```bash
# Create
python -m venv venv

# Activate — Windows (PowerShell)
venv\Scripts\Activate.ps1

# Activate — Windows (CMD)
venv\Scripts\activate.bat

# Activate — macOS / Linux
source venv/bin/activate
```

**3. Install all dependencies:**

```bash
pip install -r requirements.txt
```

**4. Create your `.env` file:**

```bash
# Copy the template and edit with your values
copy .env.example .env       # Windows
cp .env.example .env         # macOS/Linux
```

---

## 6. Running the Services

You need **three separate terminal windows**. In each, activate the virtual environment first (or use the full venv path as shown below).

> **Tip for Windows PowerShell:** Use the full path to avoid activation issues.

### Terminal 1 — Student Microservice (Port 8001)

```bash
# Using full venv path (recommended on Windows)
d:\path\to\microservices-fastapi\venv\Scripts\uvicorn.exe main:app --reload --port 8001

# Or after activating venv
cd student-service
uvicorn main:app --reload --port 8001
```

Expected output:

```
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### Terminal 2 — Course Microservice (Port 8002)

```bash
d:\path\to\microservices-fastapi\venv\Scripts\uvicorn.exe main:app --reload --port 8002
# (run from inside course-service/)
```

### Terminal 3 — API Gateway (Port 8000)

```bash
d:\path\to\microservices-fastapi\venv\Scripts\uvicorn.exe main:app --reload --port 8000
# (run from inside gateway/)
```

### Verify All Services Are Up

```powershell
Invoke-RestMethod http://localhost:8000/   # Gateway
Invoke-RestMethod http://localhost:8001/   # Student Service
Invoke-RestMethod http://localhost:8002/   # Course Service
```

---

## 7. API Reference

### API Gateway (Port 8000)

The Gateway is the **only entry point** for clients. It authenticates requests and proxies them to the correct downstream microservice.

#### Authentication Endpoints (Public)

| Method | Endpoint      | Description                          |
| ------ | ------------- | ------------------------------------ |
| POST   | `/auth/token` | Login — returns a JWT bearer token   |
| GET    | `/auth/me`    | Returns the currently logged-in user |

**POST `/auth/token`** — Request body (form data):

```
username=admin&password=secret
```

Response:

```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in_minutes": 30,
  "username": "admin",
  "role": "admin"
}
```

---

#### Student Routes via Gateway (🔒 JWT Required)

| Method | Endpoint                         | Description            |
| ------ | -------------------------------- | ---------------------- |
| GET    | `/gateway/students`              | Get all students       |
| GET    | `/gateway/students/{student_id}` | Get a student by ID    |
| POST   | `/gateway/students`              | Create a new student   |
| PUT    | `/gateway/students/{student_id}` | Update a student by ID |
| DELETE | `/gateway/students/{student_id}` | Delete a student by ID |

---

#### Course Routes via Gateway (🔒 JWT Required)

| Method | Endpoint                       | Description           |
| ------ | ------------------------------ | --------------------- |
| GET    | `/gateway/courses`             | Get all courses       |
| GET    | `/gateway/courses/{course_id}` | Get a course by ID    |
| POST   | `/gateway/courses`             | Create a new course   |
| PUT    | `/gateway/courses/{course_id}` | Update a course by ID |
| DELETE | `/gateway/courses/{course_id}` | Delete a course by ID |

---

### Student Microservice (Port 8001)

Direct access (bypasses the gateway and auth — internal use only).

| Method | Endpoint                     | Description            |
| ------ | ---------------------------- | ---------------------- |
| GET    | `/`                          | Health check           |
| GET    | `/api/students`              | Get all students       |
| GET    | `/api/students/{student_id}` | Get a student by ID    |
| POST   | `/api/students`              | Create a new student   |
| PUT    | `/api/students/{student_id}` | Update a student by ID |
| DELETE | `/api/students/{student_id}` | Delete a student by ID |

**Student Schema:**

```json
{
  "id": 1,
  "name": "John Doe",
  "age": 20,
  "email": "john@example.com",
  "course": "Computer Science"
}
```

**StudentCreate Schema** (for POST):

```json
{
  "name": "Alice Brown",
  "age": 21,
  "email": "alice@example.com",
  "course": "Cybersecurity"
}
```

**StudentUpdate Schema** (for PUT — all fields optional):

```json
{
  "age": 22,
  "email": "newemail@example.com"
}
```

**Pre-seeded data:**

| ID  | Name        | Age | Course                 |
| --- | ----------- | --- | ---------------------- |
| 1   | John Doe    | 20  | Computer Science       |
| 2   | Jane Smith  | 22  | Information Technology |
| 3   | Bob Johnson | 21  | Software Engineering   |

---

### Course Microservice (Port 8002)

Direct access (bypasses gateway — internal use only).

| Method | Endpoint                   | Description           |
| ------ | -------------------------- | --------------------- |
| GET    | `/`                        | Health check          |
| GET    | `/api/courses`             | Get all courses       |
| GET    | `/api/courses/{course_id}` | Get a course by ID    |
| POST   | `/api/courses`             | Create a new course   |
| PUT    | `/api/courses/{course_id}` | Update a course by ID |
| DELETE | `/api/courses/{course_id}` | Delete a course by ID |

**Course Schema:**

```json
{
  "id": 1,
  "title": "Computer Science",
  "credits": 4,
  "instructor": "Dr. Alan Smith",
  "description": "Core CS concepts including algorithms and data structures."
}
```

**Pre-seeded data:**

| ID  | Title                  | Credits | Instructor        |
| --- | ---------------------- | ------- | ----------------- |
| 1   | Computer Science       | 4       | Dr. Alan Smith    |
| 2   | Information Technology | 3       | Dr. Sarah Johnson |
| 3   | Software Engineering   | 4       | Dr. Mark Williams |
| 4   | Cybersecurity          | 3       | Dr. Linda Park    |

---

## 8. Authentication Flow

This project implements **JWT (JSON Web Token)** Bearer authentication on all `/gateway/*` routes.

### How JWT Works

```
1. Client sends credentials (username + password)
          │
          ▼
2. Gateway verifies credentials against FAKE_USERS_DB
   (loaded from .env)
          │
          ▼
3. Gateway creates a signed JWT token
   Payload: { "sub": "admin", "role": "admin", "exp": <timestamp> }
   Signed with:  SECRET_KEY from .env  +  ALGORITHM (HS256)
          │
          ▼
4. Client stores the token and sends it with every request:
   Header:  Authorization: Bearer eyJhbGci...
          │
          ▼
5. Gateway decodes + validates the token on each protected request.
   If valid → forward to microservice.
   If invalid/expired → return 401 Unauthorized.
```

### Demo Users

| Username  | Password  | Role   |
| --------- | --------- | ------ |
| `admin`   | `secret`  | admin  |
| `student` | `pass123` | viewer |

> Credentials are defined in `.env` (`ADMIN_USERNAME`, `ADMIN_PASSWORD`, etc.)

### Token Expiry

Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 30 minutes). After expiry, call `POST /auth/token` again to get a fresh token.

---

## 9. Request Logging

The Gateway includes a **logging middleware** (Activity 3) that automatically logs every incoming request and outgoing response.

### Log Format

```
2026-02-25 20:30:01 | INFO     | [REQ  #1740495601234] POST    /auth/token | client=127.0.0.1
2026-02-25 20:30:01 | INFO     | [RES  #1740495601234] status=200 | 48.32 ms
2026-02-25 20:30:02 | INFO     | [REQ  #1740495602891] GET     /gateway/students | client=127.0.0.1
2026-02-25 20:30:02 | INFO     | [PROXY] STUDENT → GET http://localhost:8001/api/students
2026-02-25 20:30:02 | INFO     | [RES  #1740495602891] status=200 | 12.07 ms
```

### Response Headers Added

Every response from the Gateway includes two extra headers:

| Header              | Example Value   | Purpose                          |
| ------------------- | --------------- | -------------------------------- |
| `X-Request-Id`      | `1740495601234` | Unique ID to trace a request     |
| `X-Process-Time-Ms` | `48.32`         | Total time taken to process (ms) |

---

## 10. Error Handling

The Gateway implements **global exception handlers** (Activity 4) that return consistent, structured JSON for all error types.

### Error Response Format

```json
{
  "error": "ERROR_LABEL",
  "message": "Human-readable description of what went wrong.",
  "path": "/gateway/students/999",
  "method": "GET"
}
```

### Error Types & HTTP Status Codes

| Scenario                             | Status Code | `error` label           |
| ------------------------------------ | ----------- | ----------------------- |
| Missing / invalid JWT token          | `401`       | `UNAUTHORIZED`          |
| Wrong username or password           | `401`       | `INVALID_CREDENTIALS`   |
| Resource not found (e.g., bad ID)    | `404`       | `NOT_FOUND`             |
| Unknown gateway service name         | `404`       | `SERVICE_NOT_FOUND`     |
| Request body fails Pydantic check    | `422`       | `VALIDATION_ERROR`      |
| Microservice is down / unreachable   | `503`       | `SERVICE_UNAVAILABLE`   |
| Microservice did not respond in time | `504`       | `GATEWAY_TIMEOUT`       |
| Unexpected server crash              | `500`       | `INTERNAL_SERVER_ERROR` |

### Example Error Responses

**401 — Bad credentials:**

```json
{
  "error": "INVALID_CREDENTIALS",
  "message": "Incorrect username or password."
}
```

**422 — Validation failure:**

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Request body or parameters failed validation.",
  "details": [
    {
      "field": "body → age",
      "message": "Input should be a valid integer",
      "type": "int_parsing"
    }
  ]
}
```

**503 — Microservice down:**

```json
{
  "error": "SERVICE_UNAVAILABLE",
  "message": "Cannot connect to 'student' service at http://localhost:8001.",
  "hint": "Make sure the student-service is running."
}
```

---

## 11. Testing with Swagger UI

FastAPI automatically generates interactive API documentation. Open these URLs in your browser while the services are running:

| Service         | Swagger UI URL             |
| --------------- | -------------------------- |
| **API Gateway** | http://localhost:8000/docs |
| **Student Svc** | http://localhost:8001/docs |
| **Course Svc**  | http://localhost:8002/docs |

### Step-by-Step: Testing a Protected Route via Swagger

1. **Open** [http://localhost:8000/docs](http://localhost:8000/docs)
2. **Find** `POST /auth/token` → click **Try it out**
3. **Enter** `username: admin`, `password: secret` → click **Execute**
4. **Copy** the `access_token` value from the response
5. **Click** the **🔒 Authorize** button at the top of the page
6. **Paste** the token in the `Value` field → click **Authorize**
7. **Now** all 🔒 locked endpoints are unlocked — try `GET /gateway/students`

### Step-by-Step: Testing the Full Chain

```
Test 1 — Direct Student Service
  → GET http://localhost:8001/api/students
  → Should return 3 students (no auth needed — direct access)

Test 2 — Via Gateway WITHOUT token
  → GET http://localhost:8000/gateway/students
  → Should return 401 Unauthorized

Test 3 — Get a token
  → POST http://localhost:8000/auth/token  (username=admin, password=secret)
  → Copy access_token

Test 4 — Via Gateway WITH token
  → GET http://localhost:8000/gateway/students
  → Header: Authorization: Bearer <token>
  → Should return same 3 students ✅

Test 5 — Gateway to Course Service
  → GET http://localhost:8000/gateway/courses
  → Header: Authorization: Bearer <token>
  → Should return 4 courses ✅
```

---

## 12. Activities Summary

This project was built in stages. Here is what each activity added:

### Activity 1 — Course Microservice

- Created `course-service/` with the same 4-layer architecture as `student-service`
- Runs independently on **port 8002**
- Added `/gateway/courses/*` routes to the API Gateway
- Pre-seeded with 4 courses (Computer Science, IT, Software Engineering, Cybersecurity)

### Activity 2 — JWT Authentication

- `POST /auth/token` endpoint issues signed JWT tokens
- All `/gateway/*` routes require a valid `Authorization: Bearer <token>` header
- Tokens expire after 30 minutes (configurable via `.env`)
- Implemented using `python-jose` for JWT encoding/decoding
- Passwords hashed with `passlib` (sha256_crypt scheme)

### Activity 3 — Request Logging Middleware

- Every HTTP request logged with: method, path, client IP, and a unique request ID
- Every HTTP response logged with: status code and processing time in milliseconds
- Two custom headers added to all responses: `X-Request-Id` and `X-Process-Time-Ms`
- Implemented as a FastAPI `@app.middleware("http")` — runs for every request automatically

### Activity 4 — Enhanced Error Handling

- Global `@app.exception_handler` for: `HTTPException`, `RequestValidationError`, `Exception`
- All errors return a consistent JSON structure with `error`, `message`, `path`, `method`
- `503 SERVICE_UNAVAILABLE` when a downstream service is unreachable (with a helpful hint)
- `504 GATEWAY_TIMEOUT` when a service doesn't respond in time
- `422 VALIDATION_ERROR` with per-field details when the request body is malformed
- Unexpected server errors return `500` without exposing internal stack traces

### `.env` Secret Management

- All secrets extracted from code into a root `.env` file
- `python-dotenv` with `find_dotenv()` used so all services automatically find the same file
- `.env.example` template provided for onboarding new developers
- `.gitignore` ensures `.env` is never accidentally committed

---

## Quick Reference Card

```
# START ALL SERVICES (Windows — 3 terminals)

# Terminal 1
cd student-service
..\venv\Scripts\uvicorn.exe main:app --reload --port 8001

# Terminal 2
cd course-service
..\venv\Scripts\uvicorn.exe main:app --reload --port 8002

# Terminal 3
cd gateway
..\venv\Scripts\uvicorn.exe main:app --reload --port 8000

# QUICK TEST (PowerShell)
$r = Invoke-RestMethod -Uri "http://localhost:8000/auth/token" `
     -Method POST -Body "username=admin&password=secret" `
     -ContentType "application/x-www-form-urlencoded"
$h = @{ Authorization = "Bearer " + $r.access_token }
Invoke-RestMethod "http://localhost:8000/gateway/students" -Headers $h
Invoke-RestMethod "http://localhost:8000/gateway/courses"  -Headers $h
```

---

_Built for SLIIT MTIT Practical 3 — Microservices with FastAPI_
