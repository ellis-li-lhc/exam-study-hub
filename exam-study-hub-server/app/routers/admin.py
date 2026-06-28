# 管理员接口：用户管理（列表 / 改角色 / 删除）。全部要求管理员权限。
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_admin
from app.crud import user as crud_user
from app.crud import state as crud_state
from app.models.user import User
from app.schemas.auth import UserAdminItem, RoleUpdate, PasswordUpdate
from app.schemas.state import UserStateRead

router = APIRouter(prefix="/api/admin/users", tags=["admin"])


@router.get("", response_model=list[UserAdminItem])
def list_users(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return crud_user.list_users(db)


@router.get("/{user_id}/state", response_model=UserStateRead)
def get_user_state(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """查看某用户的填报信息（报考档案/诊断/进度，存于 user_states）。"""
    target = crud_user.get_by_id(db, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    state = crud_state.get_state(db, user_id)
    if state is None:
        return UserStateRead()
    return UserStateRead(
        app_state=state.app_state,
        english_extras=state.english_extras,
        vocab_progress=state.vocab_progress,
    )


@router.patch("/{user_id}/role", response_model=UserAdminItem)
def update_role(
    user_id: int,
    data: RoleUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    target = crud_user.get_by_id(db, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    # 防止管理员把自己降级后失去管理入口。
    if target.id == admin.id and data.role != "admin":
        raise HTTPException(status_code=400, detail="不能取消自己的管理员权限")
    return crud_user.update_role(db, target, data.role)


@router.patch("/{user_id}/password", response_model=UserAdminItem)
def reset_password(
    user_id: int,
    data: PasswordUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理员重置用户密码（设置新密码覆盖，明文密码无法查看）。"""
    target = crud_user.get_by_id(db, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    crud_user.set_password(db, target, data.password)
    return target


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    target = crud_user.get_by_id(db, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    crud_user.delete_user(db, target)
    return None
