from pydantic import BaseModel


class ScoreRead(BaseModel):
    year: int
    category_name: str          # 科类名，如 专升本经管类
    major_category: str | None = None   # 对应的专业类别，如 经济管理类
    score: int | None = None
    tuition: int | None = None  # 该科类学费(元/年)，省定标准


class SourceRead(BaseModel):
    """数据来源与可信度（文档 §7）。当前由院校投档线数据派生。"""
    provider: str | None = None     # 来源机构，如 江苏省教育考试院
    year: int | None = None         # 数据年度
    line_type: str | None = None    # 分数线类型，如 院校投档线
    url: str | None = None          # 官方来源链接
    confidence: str = "none"        # verified=官方已核实 / none=暂无数据


class InstitutionRead(BaseModel):
    code: str
    name: str
    province: str               # 省份 code
    city: str | None = None
    duration: str | None = None
    tuition: int | None = None
    teaching_site: str | None = None
    degree: str | None = None
    majors: list[str] = []      # 该院校开设的专业 code（按科类推导）
    scores: list[ScoreRead] = []
    source: SourceRead | None = None
