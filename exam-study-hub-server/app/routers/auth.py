# 鉴权接口：邮箱验证、注册、登录、查询当前用户。
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.crud import user as crud_user
from app.models.user import EmailVerificationCode, PasswordResetCode, User
from app.schemas.auth import (
    EmailCodeRequest,
    EmailCodeResponse,
    LoginRequest,
    PasswordResetRequest,
    PasswordResetResponse,
    RegisterRequest,
    TokenResponse,
    UserRead,
)
from app.services.email_verification import (
    EmailServiceError,
    code_matches,
    digest_password_reset_code,
    digest_verification_code,
    generate_verification_code,
    normalize_email,
    password_reset_code_matches,
    send_password_reset_email,
    send_verification_email,
    verify_turnstile,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    """Cloudflare Tunnel 会传入真实 IP；本地开发则回退到连接 IP。"""
    cloudflare_ip = request.headers.get("cf-connecting-ip", "").strip()
    if cloudflare_ip:
        return cloudflare_ip[:64]
    return (request.client.host if request.client else "unknown")[:64]


@router.post("/email-code", response_model=EmailCodeResponse)
async def send_email_code(
    data: EmailCodeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """通过 Turnstile 后发送六位注册验证码。"""
    email = normalize_email(str(data.email))
    request_ip = _client_ip(request)
    now = datetime.now(timezone.utc)

    if crud_user.get_by_email(db, email):
        raise HTTPException(status_code=409, detail="该邮箱已被注册")

    cooldown_since = now - timedelta(seconds=settings.email_code_resend_seconds)
    recently_sent = db.scalar(
        select(EmailVerificationCode.id)
        .where(
            EmailVerificationCode.email == email,
            EmailVerificationCode.created_at > cooldown_since,
        )
        .limit(1)
    )
    if recently_sent:
        raise HTTPException(
            status_code=429,
            detail=f"请在 {settings.email_code_resend_seconds} 秒后再次获取验证码",
        )

    email_daily_count = db.scalar(
        select(func.count(EmailVerificationCode.id)).where(
            EmailVerificationCode.email == email,
            EmailVerificationCode.created_at > now - timedelta(days=1),
        )
    ) or 0
    if email_daily_count >= settings.email_code_daily_limit:
        raise HTTPException(status_code=429, detail="该邮箱今日获取验证码次数已达上限")

    ip_hourly_count = db.scalar(
        select(func.count(EmailVerificationCode.id)).where(
            EmailVerificationCode.request_ip == request_ip,
            EmailVerificationCode.created_at > now - timedelta(hours=1),
        )
    ) or 0
    if ip_hourly_count >= settings.email_code_ip_hourly_limit:
        raise HTTPException(status_code=429, detail="当前网络获取验证码过于频繁，请稍后重试")

    try:
        if not await verify_turnstile(data.turnstile_token, request_ip):
            raise HTTPException(status_code=400, detail="人机验证未通过，请重新验证")
        code = generate_verification_code()
        await send_verification_email(email, code)
    except EmailServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # 发送成功后才记录，避免第三方故障消耗用户限额。
    db.add(
        EmailVerificationCode(
            email=email,
            code_digest=digest_verification_code(email, code),
            request_ip=request_ip,
            expires_at=now + timedelta(minutes=settings.email_code_expire_minutes),
        )
    )
    # 只保留近期限流所需的记录，防止表无限增长。
    db.execute(
        delete(EmailVerificationCode).where(
            EmailVerificationCode.created_at < now - timedelta(days=2)
        )
    )
    db.commit()
    return EmailCodeResponse(
        expires_in=settings.email_code_expire_minutes * 60,
        resend_after=settings.email_code_resend_seconds,
    )


@router.post("/password-reset/code", response_model=EmailCodeResponse)
async def send_password_reset_code(
    data: EmailCodeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """通过 Turnstile 发送密码找回验证码。

    无论邮箱是否注册都返回相同结果，避免通过接口枚举用户邮箱。
    """
    email = normalize_email(str(data.email))
    request_ip = _client_ip(request)
    now = datetime.now(timezone.utc)

    cooldown_since = now - timedelta(seconds=settings.email_code_resend_seconds)
    recently_sent = db.scalar(
        select(PasswordResetCode.id)
        .where(
            PasswordResetCode.email == email,
            PasswordResetCode.created_at > cooldown_since,
        )
        .limit(1)
    )
    if recently_sent:
        raise HTTPException(
            status_code=429,
            detail=f"请在 {settings.email_code_resend_seconds} 秒后再次获取验证码",
        )

    email_daily_count = db.scalar(
        select(func.count(PasswordResetCode.id)).where(
            PasswordResetCode.email == email,
            PasswordResetCode.created_at > now - timedelta(days=1),
        )
    ) or 0
    if email_daily_count >= settings.email_code_daily_limit:
        raise HTTPException(status_code=429, detail="该邮箱今日获取验证码次数已达上限")

    ip_hourly_count = db.scalar(
        select(func.count(PasswordResetCode.id)).where(
            PasswordResetCode.request_ip == request_ip,
            PasswordResetCode.created_at > now - timedelta(hours=1),
        )
    ) or 0
    if ip_hourly_count >= settings.email_code_ip_hourly_limit:
        raise HTTPException(status_code=429, detail="当前网络获取验证码过于频繁，请稍后重试")

    try:
        if not await verify_turnstile(data.turnstile_token, request_ip, "password-reset"):
            raise HTTPException(status_code=400, detail="人机验证未通过，请重新验证")

        code = generate_verification_code()
        user = crud_user.get_by_email(db, email)
        if user is not None:
            await send_password_reset_email(email, code)
        # 未注册邮箱也留一条不发送邮件的记录，让冷却、日限额和 IP 限流对所有请求一致。
        db.add(
            PasswordResetCode(
                email=email,
                code_digest=digest_password_reset_code(email, code),
                request_ip=request_ip,
                expires_at=now + timedelta(minutes=settings.email_code_expire_minutes),
            )
        )
        db.execute(
            delete(PasswordResetCode).where(
                PasswordResetCode.created_at < now - timedelta(days=2)
            )
        )
        db.commit()
    except EmailServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return EmailCodeResponse(
        expires_in=settings.email_code_expire_minutes * 60,
        resend_after=settings.email_code_resend_seconds,
    )


@router.post("/password-reset", response_model=PasswordResetResponse)
def reset_password(data: PasswordResetRequest, db: Session = Depends(get_db)):
    """校验密码找回验证码并设置新密码。"""
    email = normalize_email(str(data.email))
    now = datetime.now(timezone.utc)
    verification = db.scalars(
        select(PasswordResetCode)
        .where(
            PasswordResetCode.email == email,
            PasswordResetCode.consumed_at.is_(None),
            PasswordResetCode.expires_at > now,
        )
        .order_by(PasswordResetCode.created_at.desc())
        .with_for_update()
        .limit(1)
    ).first()
    user = crud_user.get_by_email(db, email)

    if verification is None or user is None:
        raise HTTPException(status_code=400, detail="验证码错误或已过期，请重新获取")
    if verification.attempts >= settings.email_code_max_attempts:
        raise HTTPException(status_code=400, detail="验证码已失效，请重新获取")
    if not password_reset_code_matches(email, data.verification_code, verification.code_digest):
        verification.attempts += 1
        if verification.attempts >= settings.email_code_max_attempts:
            verification.consumed_at = now
        db.commit()
        raise HTTPException(status_code=400, detail="验证码错误")

    crud_user.set_password(db, user, data.new_password, commit=False)
    verification.consumed_at = now
    # 同一邮箱的其他未使用验证码同时失效，避免旧验证码继续改密。
    db.execute(
        update(PasswordResetCode)
        .where(
            PasswordResetCode.email == email,
            PasswordResetCode.id != verification.id,
            PasswordResetCode.consumed_at.is_(None),
        )
        .values(consumed_at=now)
    )
    db.commit()
    return PasswordResetResponse()


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """校验邮箱验证码并注册新账号，成功后直接返回 token。"""
    email = normalize_email(str(data.email))
    now = datetime.now(timezone.utc)
    if crud_user.get_by_username(db, data.username):
        raise HTTPException(status_code=409, detail="用户名已被注册")
    if crud_user.get_by_email(db, email):
        raise HTTPException(status_code=409, detail="邮箱已被注册")

    verification = db.scalars(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.email == email,
            EmailVerificationCode.consumed_at.is_(None),
            EmailVerificationCode.expires_at > now,
        )
        .order_by(EmailVerificationCode.created_at.desc())
        .with_for_update()
        .limit(1)
    ).first()
    if not verification:
        raise HTTPException(status_code=400, detail="验证码不存在或已过期，请重新获取")
    if verification.attempts >= settings.email_code_max_attempts:
        raise HTTPException(status_code=400, detail="验证码已失效，请重新获取")
    if not code_matches(email, data.verification_code, verification.code_digest):
        verification.attempts += 1
        if verification.attempts >= settings.email_code_max_attempts:
            verification.consumed_at = now
        db.commit()
        raise HTTPException(status_code=400, detail="验证码错误")

    try:
        verification.consumed_at = now
        user = crud_user.create_user(
            db,
            data.username,
            data.password,
            email,
            email_verified_at=now,
            commit=False,
        )
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="用户名或邮箱已被注册") from exc

    token = create_access_token(user.id, user.password_version)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """账号密码登录，返回 token。"""
    user = crud_user.authenticate(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(user.id, user.password_version)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    """用 token 换取当前登录用户信息，前端可用来校验登录态。"""
    return UserRead.model_validate(user)
