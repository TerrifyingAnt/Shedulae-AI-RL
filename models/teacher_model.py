from .science_degree_types import ScienceDegreeType
from .subject_model import Subject

class Teacher:

    def __init__(self, name: str, science_degree: ScienceDegreeType, subjects: list[Subject]):
        self.name = name
        self.science_degree = science_degree
        self.subjects = subjects