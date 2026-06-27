# SQLAlchemy 2.0 的声明基类。
# 所有数据库表模型（models/ 里的类）都要继承这个 Base，
# Alembic 也靠 Base.metadata 知道“项目里一共有哪些表”。
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""
    pass
