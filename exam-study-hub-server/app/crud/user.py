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
