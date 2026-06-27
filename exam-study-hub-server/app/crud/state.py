# 用户云端状态的数据库读写。
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import UserState
from app.schemas.state import UserStateUpdate


def get_state(db: Session, user_id: int) -> UserState | None:
    return db.scalars(select(UserState).where(UserState.user_id == user_id)).first()


def upsert_state(db: Session, user_id: int, data: UserStateUpdate) -> UserState:
    """更新用户状态；没有则新建。只覆盖本次传了的字段（非 None）。"""
    state = get_state(db, user_id)
    if state is None:
        state = UserState(user_id=user_id)
        db.add(state)

    # exclude_unset=True：只拿前端这次真正传了的字段，避免把未传字段误清空。
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(state, field, value)

    db.commit()
    db.refresh(state)
    return state
