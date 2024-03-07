from .subject_model import Subject

class Course:
    def __init__(self, number: int, course_name: str, subjects: list[Subject]):
        self.number = number
        self.course_name = course_name
        self.subjects = subjects
