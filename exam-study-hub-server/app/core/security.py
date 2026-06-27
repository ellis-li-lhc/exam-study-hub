# 鉴权相关的“纯函数”工具：密码哈希校验、生成/解析 JWT。
# 这一层不碰数据库、不碰 HTTP，只做加解密和编解码。
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt  # PyJWT

from app.core.config import settings


# —— 密码哈希 ——
# 绝不能明文存密码。注册时把密码哈希后存库，登录时把输入的密码再哈希对比。
# bcrypt 内部会带“盐”，相同密码每次哈希结果都不同，但 checkpw 能正确校验。

def hash_password(plain: str) -> str:
    """把明文密码哈希成可入库的字符串。"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文密码与库里的哈希是否匹配。"""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        # 库里存的哈希格式异常时，直接判为不匹配，避免抛错。
        return False


# —— JWT ——
# 登录成功后签发一个 token 给前端，前端之后每次请求都带上它。
# token 里只放“用户是谁”（sub=user_id）和过期时间，不放敏感信息。

def create_access_token(user_id: int) -> str:
    """根据用户 id 生成一个带过期时间的 JWT。"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int | None:
    """解析 JWT，校验签名与过期时间。成功返回 user_id，失败返回 None。"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except (jwt.InvalidTokenError, ValueError):
        return None
