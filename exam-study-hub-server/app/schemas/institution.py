from pydantic import BaseModel


class ScoreRead(BaseModel):
    year: int
    category_name: str          # 科类名，如 专升本经管类
    major_category: str | None = None   # 对应的专业类别，如 经济管理类
    score: int | None = None


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
