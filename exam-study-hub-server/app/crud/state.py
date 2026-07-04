# 用户云端状态的数据库读写。
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import UserState
from app.schemas.state import UserStateUpdate


class StateVersionConflict(Exception):
    """客户端基于旧版本保存，可能覆盖其他设备的新进度。"""

    def __init__(self, server_version: int):
        self.server_version = server_version
        super().__init__(f"云端进度已更新，请刷新后再保存（当前版本 {server_version}）")


def get_state(db: Session, user_id: int) -> UserState | None:
    return db.scalars(select(UserState).where(UserState.user_id == user_id)).first()


def upsert_state(db: Session, user_id: int, data: UserStateUpdate) -> UserState:
    """更新用户状态；没有则新建。只覆盖本次传了的字段（非 None）。"""
    state = get_state(db, user_id)
    if state is None:
        state = UserState(user_id=user_id)
        db.add(state)
        db.flush()
    elif data.client_version is not None and data.client_version != state.sync_version:
        raise StateVersionConflict(state.sync_version)

    # exclude_unset=True：只拿前端这次真正传了的字段，避免把未传字段误清空。
    changes = data.model_dump(exclude_unset=True, exclude={"client_version"})
    for field, value in changes.items():
        setattr(state, field, value)
    state.sync_version = int(state.sync_version or 0) + 1

    db.commit()
    db.refresh(state)
    return state
