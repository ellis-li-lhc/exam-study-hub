# FastAPI 是 Web 框架本体
from fastapi import FastAPI, Depends
# CORS 中间件：解决“前端在 5173、后端在 8000，浏览器默认禁止跨域访问”的问题
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

# 导入我们自己写的配置和路由
from app.core.config import settings
from app.routers import majors, provinces, institutions, questions, auth, state, admin
from app.db.session import get_db

# 创建 FastAPI 应用实例，title 会显示在 /docs 文档页顶部
app = FastAPI(title="exam-study-hub API")

# 注册 CORS 中间件，允许前端跨域调用本后端
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,  # 允许的来源（前端地址）
    allow_credentials=True,                   # 允许携带 cookie 等凭证
    allow_methods=["*"],                      # 允许所有 HTTP 方法（GET/POST...）
    allow_headers=["*"],                      # 允许所有请求头
)

# 把 majors 这组路由挂到应用上，/api/majors 接口就生效了
app.include_router(majors.router)
app.include_router(provinces.router)
app.include_router(institutions.router)
app.include_router(questions.router)
app.include_router(auth.router)
app.include_router(state.router)
app.include_router(admin.router)


# 健康检查接口：访问 /api/health 返回 {"status": "ok"}，
# 用来快速确认“服务还活着”。这是最简单、不依赖数据库的接口。
@app.get("/api/health")
def health():
    return {"status": "ok"}


# 数据库连通性检查：访问 /api/db-check，执行一条 SELECT 1。
# 能返回 {"database": "connected"} 就说明后端到 PostgreSQL 的连接是通的。
# （这是临时验证用的接口，确认连接没问题后可以删掉。）
@app.get("/api/db-check")
def db_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}
