# BaseModel 是 Pydantic 的基类，用来定义“数据长什么样”。
from pydantic import BaseModel


# 用户“返回给前端”的数据结构。
class UserRead(BaseModel):
    username: str 
    age: int
    
# 创建用户时，前端要提交的数据（注意这里有 password，是入参）
class UserCreate(BaseModel):
    username: str
    age: int
    password: str

