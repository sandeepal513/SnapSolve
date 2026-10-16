from dataclasses import dataclass

@dataclass
class Answer:
    answer: str
    answer_text: str = ""
    explanation: str = ""
    display: str = ""       # exactly what the popup shows
