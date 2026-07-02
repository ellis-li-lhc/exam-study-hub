# 集中导入所有模型，确保它们注册到 Base.metadata，
# 这样 Alembic 的 autogenerate 才能“看见”这些表。
from app.models.catalog import (  # noqa: F401
    Major,
    MajorSubject,
    Province,
    Institution,
    AdmissionScore,
    AdmissionPlan,
    ProvinceControlScore,
    QuestionTopic,
    Question,
)
from app.models.user import (  # noqa: F401
    User,
    UserState,
)
