# BaseModel 是 Pydantic 的基类，定义“数据长什么样”。
# schema 是接口出入参的形状，和数据库模型 model 刻意分开。
from pydantic import BaseModel, ConfigDict


class MajorBase(BaseModel):
    code: str            # 专业代码，如 "business"
    name: str            # 专业名称，如 "工商管理"
    category: str        # 专业类别，如 "经济管理类"


# 创建专业时，前端要提交的数据（入参）
class MajorCreate(MajorBase):
    subjects: list[str] = []   # 统考科目，如 ["政治", "英语", "高等数学（二）"]


# 返回给前端的数据（出参）
class MajorRead(MajorBase):
    id: int
    subjects: list[str] = []
    # from_attributes=True：允许从 ORM 对象转换（虽然 subjects 我们在路由里手动拼）
    model_config = ConfigDict(from_attributes=True)
