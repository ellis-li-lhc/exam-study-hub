# APIRouter 用来把“一组相关接口”打包，再统一挂到主应用上。
# HTTPException 用来在出错时返回标准的 HTTP 错误（比如 404）。
from fastapi import APIRouter, HTTPException
# 从 user 这个 schema 文件导入（注意：是 user，不是 major！）
from app.schemas.user import UserRead, UserCreate

# 创建一个路由器：
# - prefix="/api/users"：这组接口的统一前缀，保持不变！路径参数不要写在这里
# - tags=["users"]：在 Swagger 文档里给接口分组用的标签
router = APIRouter(prefix="/api/users", tags=["users"])

# 临时假数据，将来换成“查数据库”。注意只放 username，不放 password。
_FAKE = [
    UserRead(username="ellis", age=18),
    UserRead(username="lihongchang", age=20),
]


# 接口一：GET /api/users —— 返回用户列表。
# 可选查询参数 min_age：传了就按“年龄 >= min_age”过滤；不传就返回全部。
# 关键：筛选条件用“查询参数”（URL 问号后面，如 ?min_age=18），不要用路径参数。
@router.get("", response_model=list[UserRead])
def read_users(min_age: int | None = None):
    if min_age is None:
        return _FAKE
    # 用传进来的 min_age 真正参与过滤，返回所有满足条件的用户（列表）
    return [user for user in _FAKE if user.age >= min_age]


# 接口二：GET /api/users/{username} —— 按用户名查单个用户。
# {username} 是“路径参数”，用来“定位某一个具体资源”，这才是它的正确用途。
@router.get("/{username}", response_model=UserRead)
def get_user(username: str):
    for user in _FAKE:
        if user.username == username:
            return user
    raise HTTPException(status_code=404, detail="用户不存在")



# 接口三：POST /api/users —— 创建一个新用户
# status_code=201：约定俗成，表示"创建成功"
@router.post("", response_model=UserRead, status_code=201)
def create_user(data: UserCreate):          # ← data 的类型是 schema，FastAPI 自动从 body 解析
    # 先查重：用户名已存在就返回 409（冲突）
    if any(u.username == data.username for u in _FAKE):
        raise HTTPException(status_code=409, detail="用户名已存在")
    # 创建新用户。注意：只把 username 和 age 放进返回数据，password 不返回也不外泄
    new_user = UserRead(username=data.username, age=data.age)
    _FAKE.append(new_user)
    return new_user


