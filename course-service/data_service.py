from models import Course


class CourseMockDataService:
    def __init__(self):
        self.courses = [
            Course(
                id=1,
                title="Computer Science",
                credits=4,
                instructor="Dr. Alan Smith",
                description="Core CS concepts including algorithms, data structures, and computation theory."
            ),
            Course(
                id=2,
                title="Information Technology",
                credits=3,
                instructor="Dr. Sarah Johnson",
                description="Focus on IT infrastructure, networking, databases, and enterprise systems."
            ),
            Course(
                id=3,
                title="Software Engineering",
                credits=4,
                instructor="Dr. Mark Williams",
                description="Software development lifecycle, design patterns, testing, and agile methodologies."
            ),
            Course(
                id=4,
                title="Cybersecurity",
                credits=3,
                instructor="Dr. Linda Park",
                description="Network security, cryptography, ethical hacking, and security protocols."
            ),
        ]
        self.next_id = 5

    def get_all_courses(self):
        return self.courses

    def get_course_by_id(self, course_id: int):
        return next((c for c in self.courses if c.id == course_id), None)

    def add_course(self, course_data):
        new_course = Course(id=self.next_id, **course_data.dict())
        self.courses.append(new_course)
        self.next_id += 1
        return new_course

    def update_course(self, course_id: int, course_data):
        course = self.get_course_by_id(course_id)
        if course:
            update_data = course_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(course, key, value)
            return course
        return None

    def delete_course(self, course_id: int):
        course = self.get_course_by_id(course_id)
        if course:
            self.courses.remove(course)
            return True
        return False
