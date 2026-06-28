# 诊断/阶段测试题库接口。
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.crud import question as crud_question
from app.schemas.question import QuestionGroup, QuestionItem

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.get("", response_model=list[QuestionGroup])
def read_questions(
    subjects: str = Query("", description="科目名，逗号分隔，如 政治,英语"),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """按科目返回题库知识点分组。返回结构与前端 getDiagnosticGroups 一致：
    每个知识点是一个 group，含 id/name/description/subject/questions。
    id 沿用 `科目-知识点名-序号` 方案，保证与前端原有逻辑兼容。"""
    subject_list = [s.strip() for s in subjects.split(",") if s.strip()]
    groups = []
    for topic in crud_question.topics_by_subjects(db, subject_list):
        groups.append(QuestionGroup(
            id=f"{topic.subject}-{topic.name}-{topic.sort_order}",
            name=topic.name,
            description=f"{topic.subject} · {topic.name} 高频知识点",
            subject=topic.subject,
            questions=[
                QuestionItem(
                    id=f"{topic.subject}-{topic.name}-{q.sort_order}",
                    stem=q.stem,
                    options=q.options,
                    answer=q.answer,
                )
                for q in sorted(topic.questions, key=lambda x: x.sort_order)
            ],
        ))
    # 按请求的科目顺序排序，便于前端按科目分 tab
    order = {s: i for i, s in enumerate(subject_list)}
    groups.sort(key=lambda g: order.get(g.subject, 999))
    return groups
