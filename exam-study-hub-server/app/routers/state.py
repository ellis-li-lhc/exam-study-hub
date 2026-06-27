# 用户云端状态接口：拉取 / 保存（需登录）。
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.crud import state as crud_state
from app.models.user import User
from app.schemas.state import UserStateRead, UserStateUpdate

router = APIRouter(prefix="/api/me/state", tags=["state"])


@router.get("", response_model=UserStateRead)
def read_state(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """拉取当前用户的云端状态。从未保存过则各字段为 null。"""
    state = crud_state.get_state(db, user.id)
    if state is None:
        return UserStateRead()
    return UserStateRead(
        app_state=state.app_state,
        english_extras=state.english_extras,
        vocab_progress=state.vocab_progress,
    )


@router.put("", response_model=UserStateRead)
def save_state(
    data: UserStateUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存当前用户的云端状态。只更新本次传了的字段。"""
    state = crud_state.upsert_state(db, user.id, data)
    return UserStateRead(
        app_state=state.app_state,
        english_extras=state.english_extras,
        vocab_progress=state.vocab_progress,
    )
