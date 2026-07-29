"""Resend 邮件发送、Turnstile 校验与验证码安全工具。"""
from __future__ import annotations

import hashlib
import hmac
import html
import secrets

import httpx

from app.core.config import settings


TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
RESEND_EMAIL_URL = "https://api.resend.com/emails"


class EmailServiceError(RuntimeError):
    """第三方验证或邮件服务暂时不可用。"""


def normalize_email(email: str) -> str:
    return email.strip().lower()


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def digest_verification_code(email: str, code: str) -> str:
    """使用服务端密钥生成摘要，避免六位数字被离线枚举。"""
    message = f"email-registration:{normalize_email(email)}:{code}".encode()
    return hmac.new(settings.secret_key.encode(), message, hashlib.sha256).hexdigest()


def code_matches(email: str, code: str, expected_digest: str) -> bool:
    return hmac.compare_digest(digest_verification_code(email, code), expected_digest)


async def verify_turnstile(token: str, remote_ip: str) -> bool:
    if not settings.turnstile_secret_key:
        raise EmailServiceError("Turnstile 尚未配置")

    try:
        async with httpx.AsyncClient(timeout=8.0, trust_env=False) as client:
            response = await client.post(
                TURNSTILE_VERIFY_URL,
                data={
                    "secret": settings.turnstile_secret_key,
                    "response": token,
                    "remoteip": remote_ip,
                },
            )
            response.raise_for_status()
            result = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise EmailServiceError("Turnstile 验证服务暂时不可用") from exc

    # action 由前端渲染时固定，可防止其他页面的 token 被挪用。
    return bool(result.get("success")) and result.get("action") in (None, "", "register")


async def send_verification_email(email: str, code: str) -> None:
    if not settings.resend_api_key or not settings.resend_from_email:
        raise EmailServiceError("Resend 尚未配置")

    safe_code = html.escape(code)
    expiry = settings.email_code_expire_minutes
    payload = {
        "from": settings.resend_from_email,
        "to": [normalize_email(email)],
        "subject": f"【上岸计划】注册验证码 {code}",
        "html": f"""
          <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#172033;line-height:1.7;max-width:560px;margin:auto">
            <h2 style="color:#1e3a8a">验证你的注册邮箱</h2>
            <p>你正在注册“上岸计划”，请在页面中输入下方验证码：</p>
            <div style="margin:24px 0;padding:16px 20px;border-radius:12px;background:#f3f6fc;color:#1e3a8a;font-size:30px;font-weight:700;letter-spacing:8px;text-align:center">{safe_code}</div>
            <p>验证码在 {expiry} 分钟内有效。如非你本人操作，请忽略这封邮件。</p>
          </div>
        """,
        "text": f"你的上岸计划注册验证码是 {code}，{expiry} 分钟内有效。如非你本人操作，请忽略这封邮件。",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            response = await client.post(
                RESEND_EMAIL_URL,
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise EmailServiceError("验证码邮件发送失败") from exc
