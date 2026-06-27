# 鉴权依赖：从请求头里取出 token，解析出当前登录用户。
# 路由函数参数里写 `user: User = Depends(get_current_user)` 即可“要求登录”。
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import decode_access_token
from app.crud import user as crud_user
from app.models.user import User

# HTTPBearer：自动从 Authorization: Bearer <token> 请求头里取 token，
# 并让 Swagger 文档页出现“Authorize”按钮，方便调试。
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未登录或登录已失效",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise unauthorized

    user = crud_user.get_by_id(db, user_id)
    if user is None:
        raise unauthorized
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """要求当前用户是管理员，否则 403。"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return user
