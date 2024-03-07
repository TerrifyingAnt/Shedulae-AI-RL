from .subject_types import SubjectType

class Subject:

    def __init__(self, name: str, count_per_term: int, type: SubjectType):
        self.name = name
        self.count_per_term = count_per_term
        self.type = type

        