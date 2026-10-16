from dataclasses import dataclass, field

@dataclass
class Question:
    raw: str
    question: str = ""
    options: dict = field(default_factory=dict)  # {"A": "text"}
    lettered: bool = True   # False = options had no A/B/C labels on screen
