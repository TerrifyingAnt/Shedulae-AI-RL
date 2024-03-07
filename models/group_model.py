from .course_model import Course

class Group:

    def __init__(self, name: int, course: Course):
        self.name = name
        self.course = course
