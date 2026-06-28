# 专业相关接口。现在从数据库查询（不再用假数据）。
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.crud import major as crud_major
from app.models.catalog import Major
from app.schemas.major import MajorRead, MajorCreate

router = APIRouter(prefix="/api/majors", tags=["majors"], dependencies=[Depends(get_current_user)])


def _to_read(major: Major) -> MajorRead:
    """把数据库里的 Major 对象转成接口返回的 MajorRead。
    subjects 是关联表里的对象列表，这里取出每条的 subject 字符串。"""
    return MajorRead(
        id=major.id,
        code=major.code,
        name=major.name,
        category=major.category,
        subjects=[s.subject for s in major.subjects],
    )


@router.get("", response_model=list[MajorRead])
def read_majors(db: Session = Depends(get_db)):
    return [_to_read(m) for m in crud_major.list_majors(db)]


@router.post("", response_model=MajorRead, status_code=201)
def add_major(data: MajorCreate, db: Session = Depends(get_db)):
    if crud_major.get_major_by_code(db, data.code):
        raise HTTPException(status_code=409, detail="专业代码已存在")
    return _to_read(crud_major.create_major(db, data))
