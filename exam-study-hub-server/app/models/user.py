# 用户与“用户云端状态”相关的数据库表模型。
from datetime import datetime, timezone

from sqlalchemy import String, JSON, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """账号表。密码只存哈希，绝不存明文。"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    # 角色：'user' 普通用户 / 'admin' 管理员。默认普通用户。
    role: Mapped[str] = mapped_column(String(16), default="user", server_default="user")
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
    sync_version: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="state")


class EmailVerificationCode(Base):
    """邮箱注册验证码发送记录。

    只保存带服务端密钥的 HMAC 摘要，不保存六位验证码明文。
    每次发送都留一条记录，便于按邮箱和 IP 做持久化限流。
    """
    __tablename__ = "email_verification_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    code_digest: Mapped[str] = mapped_column(String(64))
    request_ip: Mapped[str] = mapped_column(String(64), index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
