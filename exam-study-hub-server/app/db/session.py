# 负责“连接数据库”和“给每个请求发一个数据库会话”。
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# engine：数据库引擎，整个应用共用一个。它内部维护连接池。
# - pool_pre_ping=True：每次从池里取连接前先 ping 一下，避免用到已断开的连接。
# - echo=False：不打印 SQL 日志（学习调试时可临时改成 True 看真实 SQL）。
engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)

# SessionLocal：会话工厂。调用 SessionLocal() 就得到一个新的数据库会话。
# - autoflush=False / autocommit=False：由我们显式控制提交，行为更可预期。
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """FastAPI 依赖：每个请求开一个会话，请求结束后自动关闭。

    用法：在路由函数参数里写 `db: Session = Depends(get_db)`。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
