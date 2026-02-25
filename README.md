# Microservices Architecture with FastAPI

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
8. [Authentication Flow](#8-authentication-flow)
9. [Request Logging](#9-request-logging)
10. [Error Handling](#10-error-handling)
11. [Testing with Swagger UI](#11-testing-with-swagger-ui)

---

## 1. Architecture Overview

This project utilizes an **API Gateway pattern** to route client requests to the appropriate backend microservice.

```text
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
               │ Student Service   │   │  Course Service       │
               │ Port 8001         │   │  Port 8002            │
               │                   │   │                       │
               │ GET  /api/students│   │ GET  /api/courses     │
               │ POST /api/students│   │ POST /api/courses     │
               │ PUT  /api/students│   │ PUT  /api/courses     │
               │ DELETE ...        │   │ DELETE ...            │
               │                   │   │                       │
               │ [In-Memory Store] │   │ [In-Memory Store]     │
               └───────────────────┘   └───────────────────────┘
```

### The Restaurant Analogy

| Concept | In This Project |
|----------|----------------|
| Customer | Client (Browser / Postman) |
| Waiter | API Gateway (Port 8000) |
| Kitchen | Student / Course Microservices |

The client never directly calls the microservices. All requests go through the Gateway.

---

## 2. Project Structure

```text
microservices-fastapi/
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
│
├── student-service/
│   ├── main.py
│   ├── models.py
│   ├── service.py
│   └── data_service.py
│
├── course-service/
│   ├── main.py
│   ├── models.py
│   ├── service.py
│   └── data_service.py
│
├── gateway/
│   └── main.py
│
└── venv/
```

### Microservice Layer Architecture

```text
HTTP Request
     │
     ▼
main.py          ← Controller Layer
     │
     ▼
service.py       ← Business Logic Layer
     │
     ▼
data_service.py  ← Data Layer
     │
     ▼
models.py        ← Pydantic Schemas
```

---

## 3. Technology Stack

| Component | Technology | Version |
|------------|------------|----------|
| Web Framework | FastAPI | 0.104.1 |
| ASGI Server | Uvicorn | 0.24.0 |
| Validation | Pydantic | 2.5.0 |
| HTTP Client | HTTPX | 0.25.1 |
| JWT | python-jose | 3.3.0 |
| Password Hashing | passlib | 1.7.4 |
| Environment Variables | python-dotenv | 1.0.0 |
| Form Parsing | python-multipart | 0.0.6 |
| Language | Python | 3.8+ |

---

## 4. Environment Configuration

All configuration values are stored in a single `.env` file in the project root.

### Example `.env`

```ini
SECRET_KEY=super-secret-key-change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

STUDENT_SERVICE_URL=http://localhost:8001
COURSE_SERVICE_URL=http://localhost:8002

ADMIN_USERNAME=admin
ADMIN_PASSWORD=secret
VIEWER_USERNAME=student
VIEWER_PASSWORD=pass123
```

### Loading in Code

```python
from dotenv import find_dotenv, load_dotenv
import os

load_dotenv(find_dotenv())

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-key")
```

---

## 5. Setup & Installation

### Prerequisites

- Python 3.8+
- pip

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd microservices-fastapi
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

**Windows**
```bash
venv\Scripts\activate
```

**macOS/Linux**
```bash
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Create `.env` File

```bash
cp .env.example .env
```

---

## 6. Running the Services

Open **three terminals**.

### Terminal 1 – Student Service

```bash
cd student-service
uvicorn main:app --reload --port 8001
```

### Terminal 2 – Course Service

```bash
cd course-service
uvicorn main:app --reload --port 8002
```

### Terminal 3 – API Gateway

```bash
cd gateway
uvicorn main:app --reload --port 8000
```

---

## 7. API Reference

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|------------|
| POST | `/auth/token` | Login and receive JWT |
| GET | `/auth/me` | Get current user |

### Student Routes (JWT Required)

| Method | Endpoint |
|--------|----------|
| GET | `/gateway/students` |
| GET | `/gateway/students/{student_id}` |
| POST | `/gateway/students` |
| PUT | `/gateway/students/{student_id}` |
| DELETE | `/gateway/students/{student_id}` |

### Course Routes (JWT Required)

| Method | Endpoint |
|--------|----------|
| GET | `/gateway/courses` |
| GET | `/gateway/courses/{course_id}` |
| POST | `/gateway/courses` |
| PUT | `/gateway/courses/{course_id}` |
| DELETE | `/gateway/courses/{course_id}` |

---

## 8. Authentication Flow

```text
1. Client sends username + password
2. Gateway validates credentials
3. Gateway generates JWT token
4. Client sends token in Authorization header
5. Gateway validates token before forwarding request
```

Authorization Header Format:

```
Authorization: Bearer <your_token_here>
```

---

## 9. Request Logging

The Gateway logs every request and response.

Example:

```text
2026-02-25 20:30:01 | INFO | POST /auth/token | status=200
2026-02-25 20:30:02 | INFO | GET /gateway/students | status=200
```

---

## 10. Error Handling

Standardized JSON error format:

```json
{
  "error": "ERROR_LABEL",
  "message": "Description of what went wrong",
  "path": "/gateway/students/999",
  "method": "GET"
}
```

Common Errors:

- 401 Unauthorized
- 404 Not Found
- 422 Validation Error
- 503 Service Unavailable

---

## 11. Swagger UI

FastAPI automatically provides interactive documentation.

| Service | URL |
|----------|------|
| API Gateway | http://localhost:8000/docs |
| Student Service | http://localhost:8001/docs |
| Course Service | http://localhost:8002/docs |

### Testing a Protected Endpoint

1. Open `http://localhost:8000/docs`
2. Call `POST /auth/token`
3. Copy the `access_token`
4. Click **Authorize**
5. Paste token
6. Test protected endpoints

---
