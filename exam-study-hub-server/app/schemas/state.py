# 用户云端状态的出入参形状。三个字段都是“整块 JSON”，
# 内部结构由前端约定，后端不约束，方便 localStorage 直接上云。
from pydantic import BaseModel


class UserStateRead(BaseModel):
    """读取用户云端状态。未保存过时各字段为 null。"""
    app_state: dict | None = None
    english_extras: dict | None = None
    vocab_progress: dict | None = None


class UserStateUpdate(BaseModel):
    """更新用户云端状态。只传需要更新的字段，未传的保持不变。"""
    app_state: dict | None = None
    english_extras: dict | None = None
    vocab_progress: dict | None = None
