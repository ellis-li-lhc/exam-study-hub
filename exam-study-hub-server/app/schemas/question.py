from pydantic import BaseModel


class QuestionItem(BaseModel):
    id: str
    stem: str
    options: list[str]
    answer: str


class QuestionGroup(BaseModel):
    id: str
    name: str
    description: str
    subject: str
    questions: list[QuestionItem]
