# 统一响应信封中间件：把 /api 下的 JSON 响应统一封装成 {code, message, data}。
# - 成功(HTTP < 400)：{"code": 0, "message": "success", "data": <原返回体>}
# - 失败(HTTP >= 400)：{"code": <HTTP状态码>, "message": <错误信息>, "data": null}
# 仍保留原 HTTP 状态码（如 401/404），方便前端按状态做拦截（如 401 跳登录）。
import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


def _error_message(payload) -> str:
    """从 FastAPI 默认错误体里提取可读信息。"""
    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, str):
            return detail
        if isinstance(detail, list) and detail:
            first = detail[0]
            if isinstance(first, dict):
                return first.get("msg", "参数错误")
        return "请求失败"
    return "请求失败"


class EnvelopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # 只处理 /api 下、且返回 JSON 的响应；其余（文档、静态、204 等）原样返回
        if not request.url.path.startswith("/api"):
            return response
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            payload = json.loads(body.decode("utf-8")) if body else None
        except Exception:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=content_type,
            )

        if response.status_code < 400:
            wrapped = {"code": 0, "message": "success", "data": payload}
        else:
            wrapped = {"code": response.status_code, "message": _error_message(payload), "data": None}

        new_response = JSONResponse(content=wrapped, status_code=response.status_code)
        # 保留原响应头（如 CORS、WWW-Authenticate 等），content-length/type 交给 JSONResponse 重算
        for key, value in response.headers.items():
            if key.lower() not in ("content-length", "content-type"):
                new_response.headers[key] = value
        return new_response
