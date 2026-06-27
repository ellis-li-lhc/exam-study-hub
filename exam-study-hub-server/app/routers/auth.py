# 鉴权接口：注册、登录、查询当前用户。
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserRead

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """注册新账号，成功后直接返回 token（免去再登录一次）。"""
    if crud_user.get_by_username(db, data.username):
        raise HTTPException(status_code=409, detail="用户名已被注册")
    if data.email and crud_user.get_by_email(db, data.email):
        raise HTTPException(status_code=409, detail="邮箱已被注册")
    user = crud_user.create_user(db, data.username, data.password, data.email)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """账号密码登录，返回 token。"""
    user = crud_user.authenticate(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    """用 token 换取当前登录用户信息，前端可用来校验登录态。"""
    return UserRead.model_validate(user)
