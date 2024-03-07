from .class_types import ClassTypes

class Class:

    def __init__(self, name: str, class_type: ClassTypes):
        self.name = name
        self.class_type = class_type