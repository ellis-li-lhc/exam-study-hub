# 用户与“用户云端状态”相关的数据库表模型。
from datetime import datetime, timezone

from sqlalchemy import String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """账号表。密码只存哈希，绝不存明文。"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # 一个用户对应一份云端状态（1:1）。删除用户时连带删除其状态。
    state: Mapped["UserState"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class UserState(Base):
    """用户的云端状态。三个 JSON 字段分别镜像前端的三个 localStorage：
    - app_state      ← adult-upgrade-mvp-state（报考档案 + 诊断结果 + 任务/阶段进度）
    - english_extras ← english-extras-progress（造句/短语/语法 已掌握项）
    - vocab_progress ← english-vocab-progress（3500 词 已掌握项 + 当前分组）
    用整块 JSON 存储，是为了让“localStorage 上云”改动最小、同步最直接。
    """
    __tablename__ = "user_states"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    app_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    english_extras: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    vocab_progress: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="state")
