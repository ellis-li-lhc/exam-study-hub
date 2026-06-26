# APIRouter 用来把“一组相关接口”打包，再统一挂到主应用上。
from fastapi import APIRouter
# 导入上一步定义好的数据模型（注意是从 schemas 导入）
from app.schemas.major import MajorRead

# 创建一个路由器：
# - prefix="/api/majors"：这组接口的统一路径前缀
# - tags=["majors"]：在 Swagger 文档里给接口分组用的标签
router = APIRouter(prefix="/api/majors", tags=["majors"])

# 临时假数据，将来换成“查数据库”。先用它把整条链路跑通。
_FAKE = [
    MajorRead(code="business", name="工商管理", category="经济管理类",
              subjects=["政治", "英语", "高等数学（二）"]),
    MajorRead(code="law", name="法学", category="法学类",
              subjects=["政治", "英语", "民法"]),
]


# 定义接口：GET 请求，路径是 ""（即 prefix 本身 /api/majors）。
# response_model=list[MajorRead]：告诉 FastAPI 返回的是一个 MajorRead 列表，
# 它会据此校验数据、生成文档。
@router.get("", response_model=list[MajorRead])
def read_majors():
    # 直接返回假数据；FastAPI 自动把它转成 JSON 响应。
    return _FAKE
