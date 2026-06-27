from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.catalog import QuestionTopic


def topics_by_subjects(db: Session, subjects: list[str]) -> list[QuestionTopic]:
    """按科目取知识点（含题目），保持科目内顺序。"""
    if not subjects:
        return []
    stmt = (
        select(QuestionTopic)
        .where(QuestionTopic.subject.in_(subjects))
        .options(selectinload(QuestionTopic.questions))
        .order_by(QuestionTopic.subject, QuestionTopic.sort_order)
    )
    return list(db.scalars(stmt).all())
