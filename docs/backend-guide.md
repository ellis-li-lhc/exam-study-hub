# 后端开发指南（exam-study-hub-server）

本指南面向「前端转后端、正在学习 Python」的开发者，目标是用 **FastAPI + PostgreSQL** 把当前备考系统的后端从零搭起来，并跑通第一条端到端链路。

技术栈：

- **FastAPI**：Web 框架，自带交互式 API 文档（Swagger UI）。
- **Uvicorn**：ASGI 服务器，用于本地运行。
- **SQLAlchemy 2.0**：ORM，用 Python 类描述数据库表。
- **Alembic**：数据库迁移工具，管理表结构的版本变更。
- **Pydantic v2** + **pydantic-settings**：请求/响应数据校验与配置管理。
- **PostgreSQL**（驱动 psycopg 3）：关系型数据库。

> 学习期建议：先用**同步版 SQLAlchemy**（代码直观），跑通后再考虑升级为异步。

---

## 1. 仓库结构

采用 monorepo，前后端各一个目录：

```
exam-study-hub/
├── exam-study-hub-client/      # 现有 Vue 前端
└── exam-study-hub-server/      # FastAPI 后端（本指南）
```

后端内部目录结构：

```
exam-study-hub-server/
├── app/
│   ├── main.py              # FastAPI 入口，注册路由与中间件
│   ├── core/
│   │   └── config.py        # 配置（数据库 URL、CORS 等，读 .env）
│   ├── db/
│   │   ├── base.py          # SQLAlchemy Base（声明基类）
│   │   └── session.py       # 数据库引擎与会话、get_db 依赖
│   ├── models/              # SQLAlchemy 表模型（数据库结构）
│   ├── schemas/             # Pydantic 模型（接口出入参）
│   ├── crud/                # 数据库读写逻辑（与路由解耦）
│   └── routers/             # 各资源的 API 路由
├── alembic/                 # 数据库迁移脚本目录
├── alembic.ini
├── scripts/
│   └── seed.py              # 把现有 mock/json 数据灌入数据库
├── .env.example
├── .env                     # 本地配置（不提交，加入 .gitignore）
└── pyproject.toml
```

**分层思路**（理解这套分层是学后端的关键）：

- `models` 是数据库长什么样；`schemas` 是接口收发什么样，两者刻意分开。
- `crud` 只管「怎么读写数据库」；`routers` 只管「HTTP 请求进来后调用哪个 crud、返回什么」。
- 这样职责清晰，单个文件都不大，便于学习和维护。

---

## 2. 环境准备

### 2.1 Python 与虚拟环境

要求 Python 3.11+。推荐用 `uv`（快）或自带的 `venv`。

```bash
# 进入后端目录
cd exam-study-hub-server

# 方式一：venv（标准库自带）
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux

# 方式二：uv（更快，需先安装 uv）
uv venv && source .venv/bin/activate
```

### 2.2 安装依赖

```bash
pip install "fastapi[standard]" uvicorn sqlalchemy alembic "psycopg[binary]" pydantic-settings
```

依赖说明：

| 包 | 作用 |
| --- | --- |
| `fastapi[standard]` | FastAPI 及常用扩展 |
| `uvicorn` | 本地运行服务器 |
| `sqlalchemy` | ORM |
| `alembic` | 数据库迁移 |
| `psycopg[binary]` | PostgreSQL 驱动（psycopg 3） |
| `pydantic-settings` | 读取 .env 配置 |

### 2.3 安装并创建 PostgreSQL 数据库

macOS 用 Homebrew：

```bash
brew install postgresql@16
brew services start postgresql@16

# 创建数据库
createdb exam_study
```

记下连接信息，稍后写进 `.env`：用户名（默认是你的系统用户名）、密码、主机 `localhost`、端口 `5432`、数据库名 `exam_study`。

---

## 3. 配置与数据库连接

### 3.1 `.env` 与配置

`.env.example`（提交到仓库，作为模板）：

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/exam_study
CORS_ORIGINS=http://localhost:5173
```

`.env`（本地真实配置，**不要提交**，加进 `.gitignore`）。

`app/core/config.py`：

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
```

### 3.2 数据库会话

`app/db/base.py`：

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """所有模型的声明基类。"""
    pass
```

`app/db/session.py`：

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """FastAPI 依赖：每个请求一个数据库会话，结束后自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 4. 数据模型设计

对应规划文档（`adult-undergraduate-mvp-plan.md` 第 6 节）的核心数据对象。第一版先落地跑通闭环所需的表，其余按同样模式扩展。

### 4.1 核心表一览

| 表 | 说明 | 关键字段 |
| --- | --- | --- |
| `provinces` | 报考省份 | code, name |
| `majors` | 专业 | code, name, category |
| `major_subjects` | 专业的统考科目 | major_id, subject |
| `institutions` | 院校 | province_id, name, city, duration, tuition, teaching_site, degree |
| `institution_majors` | 院校开设的专业（多对多） | institution_id, major_id |
| `admission_scores` | 历年录取分数 | institution_id, major_id, year, score, line_type, source |
| `question_topics` | 题库知识点 | subject, name |
| `questions` | 诊断/测试题目 | topic_id, stem, options(JSON), answer |
| `users` | 用户（后期鉴权用） | email, hashed_password |
| `user_profiles` | 报考档案 | user_id, province_codes(JSON), exam_year, major_id, mode, hours... |
| `diagnostics` | 诊断结果 | user_id, subject_scores(JSON), knowledge_details(JSON)... |

> **重要约束（来自规划文档第 7 节）**：所有招生/分数数据都要带 `province`、`year`、`source`，避免把不同年度的数据混在一起。分数务必区分 `line_type`（省控线 / 院校线 / 专业线）。

### 4.2 SQLAlchemy 模型示例

`app/models/catalog.py`（专业、省份、院校、分数）：

```python
from sqlalchemy import ForeignKey, String, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Province(Base):
    __tablename__ = "provinces"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64))


class Major(Base):
    __tablename__ = "majors"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(64))
    subjects: Mapped[list["MajorSubject"]] = relationship(back_populates="major")


class MajorSubject(Base):
    __tablename__ = "major_subjects"
    id: Mapped[int] = mapped_column(primary_key=True)
    major_id: Mapped[int] = mapped_column(ForeignKey("majors.id"))
    subject: Mapped[str] = mapped_column(String(64))
    major: Mapped["Major"] = relationship(back_populates="subjects")


class Institution(Base):
    __tablename__ = "institutions"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    province_id: Mapped[int] = mapped_column(ForeignKey("provinces.id"))
    city: Mapped[str] = mapped_column(String(64))
    duration: Mapped[str] = mapped_column(String(32))
    tuition: Mapped[int] = mapped_column(Integer)
    teaching_site: Mapped[str] = mapped_column(String(255))
    degree: Mapped[str] = mapped_column(String(255))


class AdmissionScore(Base):
    __tablename__ = "admission_scores"
    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"))
    major_id: Mapped[int | None] = mapped_column(ForeignKey("majors.id"), nullable=True)
    year: Mapped[int] = mapped_column(Integer)
    score: Mapped[int] = mapped_column(Integer)
    line_type: Mapped[str] = mapped_column(String(32))   # province / institution / major
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
```

> 题库、用户、档案、诊断等表照此模式继续写。JSON 字段（如题目的 options、诊断的 subject_scores）用 `from sqlalchemy import JSON` 的 `Mapped[dict]` / `Mapped[list]` + `mapped_column(JSON)`。

---

## 5. 端到端示例：专业（Major）

第一刀建议从「专业」这种读多写少、且前端已有数据的资源切入，把 **模型 → schema → crud → 路由 → 文档** 整条链路跑通，后面照葫芦画瓢。

### 5.1 Pydantic schema

`app/schemas/major.py`：

```python
from pydantic import BaseModel, ConfigDict


class MajorBase(BaseModel):
    code: str
    name: str
    category: str


class MajorCreate(MajorBase):
    subjects: list[str] = []


class MajorRead(MajorBase):
    id: int
    subjects: list[str] = []
    # 允许直接从 ORM 对象转换
    model_config = ConfigDict(from_attributes=True)
```

### 5.2 CRUD

`app/crud/major.py`：

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalog import Major, MajorSubject
from app.schemas.major import MajorCreate


def list_majors(db: Session) -> list[Major]:
    return list(db.scalars(select(Major)).all())


def get_major(db: Session, major_id: int) -> Major | None:
    return db.get(Major, major_id)


def create_major(db: Session, data: MajorCreate) -> Major:
    major = Major(code=data.code, name=data.name, category=data.category)
    major.subjects = [MajorSubject(subject=s) for s in data.subjects]
    db.add(major)
    db.commit()
    db.refresh(major)
    return major
```

### 5.3 路由

`app/routers/majors.py`：

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud import major as crud_major
from app.schemas.major import MajorCreate, MajorRead

router = APIRouter(prefix="/api/majors", tags=["majors"])


@router.get("", response_model=list[MajorRead])
def read_majors(db: Session = Depends(get_db)):
    majors = crud_major.list_majors(db)
    return [
        MajorRead(id=m.id, code=m.code, name=m.name, category=m.category,
                  subjects=[s.subject for s in m.subjects])
        for m in majors
    ]


@router.post("", response_model=MajorRead, status_code=201)
def add_major(data: MajorCreate, db: Session = Depends(get_db)):
    if any(m.code == data.code for m in crud_major.list_majors(db)):
        raise HTTPException(status_code=409, detail="专业代码已存在")
    m = crud_major.create_major(db, data)
    return MajorRead(id=m.id, code=m.code, name=m.name, category=m.category,
                     subjects=[s.subject for s in m.subjects])
```

### 5.4 入口 `app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import majors

app = FastAPI(title="exam-study-hub API")

# 允许前端（localhost:5173）跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(majors.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
```

---

## 6. 数据库迁移（Alembic）

不要用 `Base.metadata.create_all()` 直接建表（学习期可临时用，但正式开发务必用迁移管理结构变更）。

### 6.1 初始化

```bash
alembic init alembic
```

编辑 `alembic/env.py`，让它知道你的模型与数据库地址：

```python
# 顶部导入
from app.core.config import settings
from app.db.base import Base
# 导入所有模型，确保它们被注册到 Base.metadata
from app.models import catalog  # noqa

# 设置数据库 URL（覆盖 alembic.ini 里的占位）
config.set_main_option("sqlalchemy.url", settings.database_url)

# 关键：让 autogenerate 能识别表结构
target_metadata = Base.metadata
```

### 6.2 生成并应用迁移

```bash
# 自动对比模型与数据库，生成迁移脚本
alembic revision --autogenerate -m "init catalog tables"

# 应用到数据库
alembic upgrade head
```

以后每次改了 `models/`，都重复「`revision --autogenerate` → 检查脚本 → `upgrade head`」。

> 注意：autogenerate 不是万能的（改列名、复杂约束可能识别不准），生成后一定**打开脚本检查**再 apply。

---

## 7. 运行与调试

```bash
uvicorn app.main:app --reload --port 8000
```

- 接口根：`http://localhost:8000`
- **交互式文档（重点）**：`http://localhost:8000/docs` —— FastAPI 自动生成的 Swagger UI，可以直接在浏览器里调接口、看出入参，学习/调试神器。
- 备用文档：`http://localhost:8000/redoc`

前端联调：把 `exam-study-hub-client` 里现在读 `src/data/*.js` 的地方，逐步改成 `fetch('http://localhost:8000/api/...')`。开发期建议在 Vite 里配 proxy，把 `/api` 转发到 `localhost:8000`，避免跨域和硬编码地址。

---

## 8. 灌入现有数据（seed）

前端 `src/data/mvp.js`（省份/专业/院校/分数）和 `docs/*.json`（题库）就是现成的种子数据。写一个一次性脚本把它们导入数据库。

`scripts/seed.py`（示意）：

```python
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.models.catalog import Province, Major, MajorSubject

PROVINCES = [{"code": "henan", "name": "河南"}, {"code": "jiangsu", "name": "江苏"}]

def run():
    db = SessionLocal()
    try:
        for p in PROVINCES:
            if not db.query(Province).filter_by(code=p["code"]).first():
                db.add(Province(**p))
        db.commit()
        # 专业、院校、分数、题库同理……题库可直接读取 docs/*.json
    finally:
        db.close()

if __name__ == "__main__":
    run()
```

运行：`python -m scripts.seed`。题库 JSON 结构已经规整（`topics -> questions`），可直接遍历写入 `question_topics` 和 `questions` 表。

---

## 9. 接口规划（按业务闭环）

按规划文档的主流程，后端大致需要这些接口（前缀 `/api`）：

| 模块 | 方法 | 路径 | 说明 |
| --- | --- | --- | --- |
| 省份 | GET | `/provinces` | 报考省份列表 |
| 专业 | GET | `/majors` | 专业列表（含统考科目） |
| 院校 | GET | `/institutions?province=&major=` | 按省份+专业查院校 |
| 院校 | GET | `/institutions/{id}` | 院校详情（含历年分数） |
| 题库 | GET | `/questions?subjects=政治,英语,...` | 按科目取诊断题 |
| 档案 | GET/PUT | `/profile` | 读取/保存报考档案 |
| 诊断 | POST | `/diagnostics` | 提交诊断答案，返回评分结果 |
| 目标分 | GET | `/target` | 目标分与分科目标分析 |
| 进度 | GET/PUT | `/progress` | 学习进度与阶段测试记录 |

> 鉴权（多用户、云同步）属于后续阶段：用 JWT（`python-jose` + `passlib[bcrypt]`），登录发 token，受保护接口用依赖校验。第一版可以先做「无登录、单用户」打通数据链路，再叠加鉴权。

---

## 10. 建议的开发顺序

1. 搭骨架：目录结构、`config`、`db/session`、`main.py`、健康检查接口跑起来。
2. 建模型 + Alembic 首次迁移，确认数据库能建表。
3. 跑通「专业」端到端（本指南第 5 节），在 `/docs` 里能调通。
4. 补齐「省份 / 院校 / 分数」只读接口，写 seed 脚本灌数据。
5. 题库接口 + 诊断提交接口（把现在前端的判分逻辑搬到后端）。
6. 档案、目标分、进度接口。
7. 前端逐个页面从读本地 mock 改为调后端接口。
8. 最后再加用户与鉴权（JWT）。

> 每完成一个资源就在 `/docs` 里手动验证一遍，确认通了再做下一个，避免一次写太多难定位问题。
