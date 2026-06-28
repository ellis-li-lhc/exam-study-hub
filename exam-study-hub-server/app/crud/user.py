# 用户相关的数据库读写。只管 ORM，不碰 HTTP。
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import hash_password, verify_password


def get_by_username(db: Session, username: str) -> User | None:
    return db.scalars(select(User).where(User.username == username)).first()


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalars(select(User).where(User.email == email)).first()


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create_user(db: Session, username: str, password: str, email: str | None = None) -> User:
    """新建用户，密码哈希后入库。"""
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, username: str, password: str) -> User | None:
    """校验账号密码。成功返回 User，失败返回 None。"""
    user = get_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def list_users(db: Session) -> list[User]:
    """列出所有用户（管理员用）。"""
    return list(db.scalars(select(User).order_by(User.id)).all())


def update_role(db: Session, user: User, role: str) -> User:
    """修改用户角色。"""
    user.role = role
    db.commit()
    db.refresh(user)
    return user


def set_password(db: Session, user: User, new_password: str) -> User:
    """管理员重置用户密码（存哈希，不保存明文）。"""
    user.hashed_password = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    """删除用户（连带其云端状态）。"""
    db.delete(user)
    db.commit()
