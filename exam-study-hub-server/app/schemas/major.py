# BaseModel 是 Pydantic 的基类，用来定义“数据长什么样”。
# FastAPI 会根据它自动做：类型校验、转成 JSON、生成接口文档。
from pydantic import BaseModel


# 定义“专业”接口返回的数据结构。
# 这是 schema（接口出入参的形状），和将来的数据库模型 model 是两回事，刻意分开。
class MajorRead(BaseModel):
    code: str            # 专业代码，比如 "business"
    name: str            # 专业名称，比如 "工商管理"
    category: str        # 专业类别，比如 "经济管理类"
    subjects: list[str] = []   # 统考科目列表，默认空列表
