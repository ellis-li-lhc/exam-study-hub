from pydantic import BaseModel


class AdminStat(BaseModel):
    key: str
    label: str
    value: int
    description: str | None = None
    tone: str = "neutral"


class ValidationIssue(BaseModel):
    severity: str
    area: str
    message: str


class ValidationSummary(BaseModel):
    passed: bool
    issues: list[ValidationIssue]


class AdminDataSummary(BaseModel):
    stats: list[AdminStat]
    validation: ValidationSummary


class AdminInstitutionItem(BaseModel):
    id: int
    code: str
    name: str
    province: str
    province_name: str
    city: str | None = None
    scores_count: int
    plans_count: int
    plan_major_count: int
    latest_score: int | None = None
    latest_score_year: int | None = None
    latest_line_type: str | None = None
    latest_source: str | None = None
    quality: str
    issues: list[str]


class InstitutionListResponse(BaseModel):
    total: int
    items: list[AdminInstitutionItem]


class ImportBatchItem(BaseModel):
    id: str
    data_type: str
    province: str
    province_name: str
    year: int
    line_type: str
    round: str | None = None
    source: str | None = None
    records_count: int
    institutions_count: int
    majors_count: int | None = None


class QuestionSubjectQuality(BaseModel):
    subject: str
    topics_count: int
    questions_count: int
    issue_count: int


class QuestionQualityResponse(BaseModel):
    subjects: list[QuestionSubjectQuality]
    issues: list[ValidationIssue]


class CatalogProvinceItem(BaseModel):
    code: str
    name: str
    note: str | None = None
    institutions_count: int
    scores_count: int
    plans_count: int
    control_scores_count: int


class CatalogMajorItem(BaseModel):
    code: str
    name: str
    category: str
    subjects: list[str]


class CatalogCategoryItem(BaseModel):
    category: str
    majors_count: int
    subjects: list[str]


class CatalogResponse(BaseModel):
    provinces: list[CatalogProvinceItem]
    categories: list[CatalogCategoryItem]
    majors: list[CatalogMajorItem]
