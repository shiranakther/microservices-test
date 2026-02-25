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

[cite_start]This project utilizes an API Gateway pattern to route client requests to the appropriate backend microservice[cite: 377, 379].



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
