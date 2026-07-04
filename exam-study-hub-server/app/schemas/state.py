# 用户云端状态的出入参形状。三个字段都是“整块 JSON”，
# 内部结构由前端约定，后端不约束，方便 localStorage 直接上云。
from datetime import datetime

from pydantic import BaseModel


class UserStateRead(BaseModel):
    """读取用户云端状态。未保存过时各字段为 null。"""
    app_state: dict | None = None
    english_extras: dict | None = None
    vocab_progress: dict | None = None
    sync_version: int = 0
    updated_at: datetime | None = None


class UserStateUpdate(BaseModel):
    """更新用户云端状态。只传需要更新的字段，未传的保持不变。"""
    app_state: dict | None = None
    english_extras: dict | None = None
    vocab_progress: dict | None = None
    # 前端基于哪个云端版本保存。为空时保持旧客户端兼容；非空且不匹配会返回 409。
    client_version: int | None = None
