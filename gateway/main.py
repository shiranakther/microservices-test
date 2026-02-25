import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
from dotenv import find_dotenv, load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext


load_dotenv(find_dotenv())


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("api_gateway")


SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback-dev-only-key")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


_admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
_admin_password: str = os.getenv("ADMIN_PASSWORD", "secret")
_viewer_username: str = os.getenv("VIEWER_USERNAME", "student")
_viewer_password: str = os.getenv("VIEWER_PASSWORD", "pass123")

FAKE_USERS_DB: dict = {
    _admin_username: {
        "username": _admin_username,
        "hashed_password": pwd_context.hash(_admin_password),
        "role": "admin",
    },
    _viewer_username: {
        "username": _viewer_username,
        "hashed_password": pwd_context.hash(_viewer_password),
        "role": "viewer",
    },
}


SERVICES: dict = {
    "student": os.getenv("STUDENT_SERVICE_URL", "http://localhost:8001"),
    "course": os.getenv("COURSE_SERVICE_URL", "http://localhost:8002"),
}


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = FAKE_USERS_DB.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Dependency — validates JWT and returns the current user payload."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": "UNAUTHORIZED",
            "message": "Invalid or expired token. Login at POST /auth/token.",
            "hint": "Authorization: Bearer <your_token>",
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
        return {"username": username, "role": payload.get("role")}
    except JWTError:
        raise credentials_exception



app = FastAPI(
    title="API Gateway",
    version="2.0.0",
    
)



@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = f"{int(time.time() * 1000)}"
    start = time.perf_counter()

    logger.info(
        "[REQ  #%s] %-7s %s | client=%s",
        request_id,
        request.method,
        request.url.path,
        request.client.host if request.client else "unknown",
    )

    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000

    logger.info("[RES  #%s] status=%d | %.2f ms", request_id, response.status_code, elapsed_ms)
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
    response.headers["X-Request-Id"] = request_id
    return response



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {
            "field": " → ".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "type": err["type"],
        }
        for err in exc.errors()
    ]
    logger.warning("[VALIDATION ERROR] %s %s → %s", request.method, request.url.path, errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request body or parameters failed validation.",
            "details": errors,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "[HTTP %d] %s %s — %s", exc.status_code, request.method, request.url.path, exc.detail
    )
    body = exc.detail if isinstance(exc.detail, dict) else {
        "error": _status_label(exc.status_code),
        "message": exc.detail,
        "path": str(request.url.path),
        "method": request.method,
    }
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("[UNHANDLED] %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred.",
            "path": str(request.url.path),
        },
    )


def _status_label(code: int) -> str:
    return {
        400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN",
        404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY", 503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }.get(code, f"HTTP_{code}")



async def forward_request(service: str, path: str, method: str, **kwargs) -> Any:
    if service not in SERVICES:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "SERVICE_NOT_FOUND",
                "message": f"No registered service: '{service}'.",
                "available_services": list(SERVICES.keys()),
            },
        )

    url = f"{SERVICES[service]}{path}"
    logger.info("[PROXY] %s → %s %s", service.upper(), method, url)

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await getattr(client, method.lower())(url, **kwargs)
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "SERVICE_UNAVAILABLE",
                    "message": f"Cannot connect to '{service}' at {SERVICES[service]}.",
                    "hint": f"Make sure the {service}-service is running.",
                },
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail={
                    "error": "GATEWAY_TIMEOUT",
                    "message": f"'{service}' service did not respond in time.",
                },
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail={"error": "SERVICE_UNAVAILABLE", "message": str(exc)},
            )

    try:
        content = response.json() if response.text else None
    except Exception:
        content = {"raw": response.text}

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=content)

    return JSONResponse(content=content, status_code=response.status_code)



@app.get("/", summary="Gateway Health Check")
def read_root():
    return {
        "message": "API Gateway is running",
        "version": "2.0.0",
        "services": SERVICES,
        "env_loaded": True,
        "auth_endpoint": "POST /auth/token",
        "docs": "/docs",
    }



@app.post("/auth/token", summary="Login — get JWT token", tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate to get a JWT bearer token.
    Credentials are read from the `.env` file.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning("[AUTH] Failed login: username='%s'", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_CREDENTIALS",
                "message": "Incorrect username or password.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    logger.info("[AUTH] User '%s' logged in (role=%s)", user["username"], user["role"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
        "username": user["username"],
        "role": user["role"],
    }


@app.get("/auth/me", summary="Who am I?", tags=["Authentication"])
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user



@app.get("/gateway/students", summary="Get all students", tags=["Students (via Gateway)"])
async def get_all_students(current_user: dict = Depends(get_current_user)):
    return await forward_request("student", "/api/students", "GET")


@app.get("/gateway/students/{student_id}", summary="Get student by ID", tags=["Students (via Gateway)"])
async def get_student(student_id: int, current_user: dict = Depends(get_current_user)):
    return await forward_request("student", f"/api/students/{student_id}", "GET")


@app.post("/gateway/students", summary="Create a student", tags=["Students (via Gateway)"])
async def create_student(request: Request, current_user: dict = Depends(get_current_user)):
    body = await request.json()
    return await forward_request("student", "/api/students", "POST", json=body)


@app.put("/gateway/students/{student_id}", summary="Update a student", tags=["Students (via Gateway)"])
async def update_student(student_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    body = await request.json()
    return await forward_request("student", f"/api/students/{student_id}", "PUT", json=body)


@app.delete("/gateway/students/{student_id}", summary="Delete a student", tags=["Students (via Gateway)"])
async def delete_student(student_id: int, current_user: dict = Depends(get_current_user)):
    return await forward_request("student", f"/api/students/{student_id}", "DELETE")



@app.get("/gateway/courses", summary="Get all courses", tags=["Courses (via Gateway)"])
async def get_all_courses(current_user: dict = Depends(get_current_user)):
    return await forward_request("course", "/api/courses", "GET")


@app.get("/gateway/courses/{course_id}", summary="Get course by ID", tags=["Courses (via Gateway)"])
async def get_course(course_id: int, current_user: dict = Depends(get_current_user)):
    return await forward_request("course", f"/api/courses/{course_id}", "GET")


@app.post("/gateway/courses", summary="Create a course", tags=["Courses (via Gateway)"])
async def create_course(request: Request, current_user: dict = Depends(get_current_user)):
    body = await request.json()
    return await forward_request("course", "/api/courses", "POST", json=body)


@app.put("/gateway/courses/{course_id}", summary="Update a course", tags=["Courses (via Gateway)"])
async def update_course(course_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    body = await request.json()
    return await forward_request("course", f"/api/courses/{course_id}", "PUT", json=body)


@app.delete("/gateway/courses/{course_id}", summary="Delete a course", tags=["Courses (via Gateway)"])
async def delete_course(course_id: int, current_user: dict = Depends(get_current_user)):
    return await forward_request("course", f"/api/courses/{course_id}", "DELETE")
