import os

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException, status
from models import Student, StudentCreate, StudentUpdate
from service import StudentService
from typing import List

# Load .env from project root (walks up from student-service/ automatically)
load_dotenv(find_dotenv())

app = FastAPI(
    title="Student Microservice",
    version="1.0.0",
   
)

student_service = StudentService()


@app.get("/")
def read_root():
    return {"message": "Student Microservice is running", "port": 8001}


@app.get("/api/students", response_model=List[Student])
def get_all_students():
    """Get all students"""
    return student_service.get_all()


@app.get("/api/students/{student_id}", response_model=Student)
def get_student(student_id: int):
    """Get a student by ID"""
    student = student_service.get_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with id={student_id} not found")
    return student


@app.post("/api/students", response_model=Student, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate):
    """Create a new student"""
    return student_service.create(student)


@app.put("/api/students/{student_id}", response_model=Student)
def update_student(student_id: int, student: StudentUpdate):
    """Update a student"""
    updated = student_service.update(student_id, student)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Student with id={student_id} not found")
    return updated


@app.delete("/api/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int):
    """Delete a student"""
    success = student_service.delete(student_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Student with id={student_id} not found")
    return None
