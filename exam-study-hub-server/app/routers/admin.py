# 管理员接口：用户管理（列表 / 改角色 / 删除）。全部要求管理员权限。
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_admin
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.auth import UserAdminItem, RoleUpdate

router = APIRouter(prefix="/api/admin/users", tags=["admin"])


@router.get("", response_model=list[UserAdminItem])
def list_users(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return crud_user.list_users(db)


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
