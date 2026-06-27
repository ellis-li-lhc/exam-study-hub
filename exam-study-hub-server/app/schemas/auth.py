# 鉴权接口的出入参形状。
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """注册入参。"""
    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    email: EmailStr | None = None


class LoginRequest(BaseModel):
    """登录入参。"""
    username: str
    password: str


class UserRead(BaseModel):
    """返回给前端的用户信息（不含密码）。"""
    id: int
    username: str
    email: EmailStr | None = None
    role: str = "user"
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """登录/注册成功后返回的令牌与用户信息。"""
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class UserAdminItem(BaseModel):
    """管理员视角的用户列表项。"""
    id: int
    username: str
    email: EmailStr | None = None
    role: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RoleUpdate(BaseModel):
    """修改用户角色的入参。"""
    role: Literal["user", "admin"]
