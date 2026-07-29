# 新项目后端搭建方案

## 1. 文档目的

本文档用于指导另一个新项目搭建后端。

新项目沿用 `exam-study-hub` 的后端技术栈和代码分层方式，但使用独立的后端工程、独立的 PostgreSQL 数据库和独立的数据库迁移记录。

本文档只讨论后端项目的开发与本地运行，不包含服务器、域名、Nginx、Cloudflare 或其他部署内容。

---

## 2. 总体方案

新项目采用以下技术栈：

| 类型 | 技术 | 用途 |
| --- | --- | --- |
| Web 框架 | FastAPI | 编写 HTTP API，并自动生成接口文档 |
| Web 服务器 | Uvicorn | 本地启动 FastAPI 应用 |
| 数据库 | PostgreSQL | 保存用户和业务数据 |
| ORM | SQLAlchemy 2.0 | 使用 Python 类操作数据库 |
| 数据库迁移 | Alembic | 管理数据库表结构版本 |
| 参数校验 | Pydantic v2 | 校验接口请求和响应数据 |
| 配置管理 | pydantic-settings | 从 `.env` 读取配置 |
| 身份认证 | JWT | 保存用户登录状态 |
| 密码安全 | bcrypt | 对用户密码进行哈希处理 |
| 自动化测试 | pytest | 测试接口和业务逻辑 |

新项目可以复用当前项目的通用基础代码，包括：

- 数据库连接与会话管理
- 环境配置读取
- 密码哈希与密码校验
- JWT 生成与解析
- 当前登录用户鉴权
- 管理员权限校验
- 统一接口响应格式
- 通用异常处理方式

当前项目中的院校、专业、题库、招生数据和学习进度属于特定业务，不应复制到新项目。

---

## 3. 项目目录结构

建议新建独立的后端工程：

```text
new-project-server/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # 环境变量和项目配置
│   │   ├── security.py         # 密码处理与 JWT
│   │   ├── deps.py             # 当前用户、管理员等公共依赖
│   │   └── envelope.py         # 统一接口响应格式
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py             # SQLAlchemy 声明基类
│   │   └── session.py          # 数据库引擎和会话
│   ├── models/                 # SQLAlchemy 数据库模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── business.py
│   ├── schemas/                # Pydantic 接口数据结构
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   └── business.py
│   ├── crud/                   # 数据库增删改查
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── business.py
│   └── routers/                # API 路由
│       ├── __init__.py
│       ├── auth.py
│       ├── users.py
│       └── business.py
├── alembic/                    # 数据库迁移脚本
├── scripts/
│   └── seed.py                 # 初始化基础数据
├── tests/                      # 自动化测试
├── .env.example                # 环境变量模板
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

## 4. 分层职责

后端按照 `models → schemas → crud → routers` 的方式分层。

### 4.1 models

`models` 用于定义数据库表、字段、索引、唯一约束和表之间的关系。

例如：

```text
app/models/user.py
app/models/task.py
```

### 4.2 schemas

`schemas` 用于定义接口接收和返回的数据格式。

数据库模型和接口模型应分开，避免把密码哈希、内部状态等字段错误地返回给前端。

常见模型包括：

```text
TaskCreate     创建任务时接收的数据
TaskUpdate     修改任务时接收的数据
TaskRead       返回给前端的数据
TaskListRead   列表接口返回的数据
```

### 4.3 crud

`crud` 负责数据库读写，不直接处理 HTTP 请求。

例如：

```text
create_task
get_task
list_tasks
update_task
delete_task
```

### 4.4 routers

`routers` 负责接收 HTTP 请求、校验权限、调用 CRUD，并返回结果。

路由层不应堆放复杂的数据库查询或大段业务计算。

---

## 5. 环境配置

在项目根目录提供 `.env.example`：

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/new_project
CORS_ORIGINS=http://localhost:5173
SECRET_KEY=change-me-to-a-random-long-string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

开发人员复制为 `.env` 后填写本地真实配置。

注意事项：

- `.env` 不提交到 Git。
- 新项目使用独立的数据库名称。
- 新项目使用独立的 JWT 密钥。
- 代码中不能硬编码数据库密码和 JWT 密钥。
- 生产环境不能继续使用示例密钥。

---

## 6. 依赖清单

第一版建议包含以下依赖：

```text
fastapi
uvicorn
sqlalchemy
alembic
psycopg[binary]
pydantic
pydantic-settings
python-dotenv
bcrypt
PyJWT
email-validator
pytest
httpx
```

完成首次安装并验证无误后，应锁定依赖版本，避免不同开发环境安装出不一致的版本。

---

## 7. 数据库连接

数据库连接集中放在 `app/db/session.py` 中。

基本要求：

- 全局只创建一个数据库引擎。
- 使用连接池管理数据库连接。
- 每个请求使用独立的数据库会话。
- 请求结束后自动关闭会话。
- 写操作由业务代码明确提交或回滚。
- 开启 `pool_pre_ping`，避免使用已经失效的连接。

数据库模型统一继承 `app/db/base.py` 中定义的 SQLAlchemy `Base`。

---

## 8. 账号与权限系统

### 8.1 用户表

第一版建立 `users` 表：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | bigint/integer | 主键 |
| username | varchar | 用户名，唯一 |
| email | varchar | 邮箱，可选，唯一 |
| hashed_password | varchar | 密码哈希 |
| role | varchar | `user` 或 `admin` |
| status | varchar | `active` 或 `disabled` |
| created_at | timestamptz | 创建时间 |
| updated_at | timestamptz | 更新时间 |

数据库只能保存密码哈希，不能保存用户的明文密码。

### 8.2 第一批认证接口

```text
POST /api/auth/register       注册
POST /api/auth/login          登录
GET  /api/auth/me             获取当前登录用户
PUT  /api/auth/password       修改密码
```

登录成功后由后端签发 JWT。JWT 至少包含：

```text
sub    用户 ID
exp    过期时间
```

### 8.3 权限控制

提供两个公共依赖：

```text
get_current_user     要求用户已经登录
get_current_admin    要求用户已经登录且角色为 admin
```

普通业务接口使用 `get_current_user`，管理接口使用 `get_current_admin`。

---

## 9. 业务表设计原则

新项目的业务表需要根据实际功能重新设计，不直接复制当前项目的业务模型。

用户业务表通常包含：

```text
id
user_id
业务字段
status
created_at
updated_at
```

设计时遵循以下原则：

1. 每条用户私有数据都要通过 `user_id` 关联用户。
2. 需要搜索、排序和统计的数据使用普通数据库字段。
3. 只有结构不固定的附加配置才使用 PostgreSQL `JSONB`。
4. 给 `user_id`、状态、时间和常用查询条件建立索引。
5. 使用外键保证数据关联正确。
6. 对不能重复的数据增加唯一约束。
7. 时间字段使用带时区的时间类型。
8. 对重要业务数据优先使用软删除，避免误删后无法恢复。
9. 状态字段使用约定好的固定值，不允许随意填写字符串。
10. 删除用户时，要明确关联业务数据是级联删除、保留还是匿名化。

不要把所有业务数据都放进一个大型 JSON 字段。大型 JSON 虽然前期开发快，但不利于查询、统计、校验和后续迁移。

---

## 10. 业务接口设计

接口统一使用 `/api` 前缀。对于后续可能发生较大变化的项目，也可以从第一版开始使用 `/api/v1`。

以“任务”模块为例：

```text
POST   /api/tasks             创建任务
GET    /api/tasks             获取当前用户的任务列表
GET    /api/tasks/{id}        获取任务详情
PUT    /api/tasks/{id}        修改任务
DELETE /api/tasks/{id}        删除任务
```

列表接口应提前考虑：

- 分页
- 状态筛选
- 关键词搜索
- 排序
- 创建时间范围

查询用户私有数据时，不能只按数据 ID 查询，必须同时限制当前用户：

```text
记录 ID = 请求中的 ID
并且 user_id = 当前登录用户 ID
```

否则可能出现用户访问或修改其他用户数据的越权问题。

---

## 11. 统一响应与错误处理

成功响应统一为：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

失败响应统一为：

```json
{
  "code": 40001,
  "message": "请求参数不正确",
  "data": null
}
```

建议统一处理以下异常：

| HTTP 状态码 | 场景 |
| --- | --- |
| 400 | 请求内容不符合业务规则 |
| 401 | 未登录或 Token 已失效 |
| 403 | 已登录但没有权限 |
| 404 | 数据不存在 |
| 409 | 数据重复或版本冲突 |
| 422 | 请求参数校验失败 |
| 500 | 未预期的服务器错误 |

服务器错误不能把数据库密码、SQL 详情、代码路径或完整异常堆栈返回给前端。

---

## 12. 数据库迁移

所有表结构变化都通过 Alembic 管理。

推荐流程：

1. 修改 SQLAlchemy 模型。
2. 生成 Alembic 迁移文件。
3. 人工检查迁移内容。
4. 在本地空数据库执行迁移。
5. 在已有测试数据的数据库执行升级测试。
6. 确认无误后提交模型和迁移文件。

禁止只修改数据库而不提交迁移文件，也不要在多人开发时随意修改已经执行过的历史迁移。

---

## 13. 初始化脚本

使用 `scripts/seed.py` 初始化新项目运行所需的数据，例如：

- 默认管理员账号
- 系统字典
- 默认分类
- 系统配置
- 业务演示数据（仅开发环境）

初始化脚本应支持重复执行，不应因数据已经存在而重复插入或直接报错。

---

## 14. 自动化测试

第一版至少覆盖：

- 健康检查接口
- 用户注册
- 用户登录
- 错误密码登录
- 未登录访问受保护接口
- 普通用户访问管理员接口
- 新增业务数据
- 查询当前用户业务数据
- 修改业务数据
- 删除业务数据
- 用户不能访问其他用户的数据
- 重复数据和无效参数处理

建议为测试使用独立数据库，避免测试代码修改开发数据库中的真实数据。

---

## 15. 开发实施顺序

### 阶段一：项目骨架

- 创建后端目录结构。
- 配置 Python 虚拟环境和依赖。
- 创建 FastAPI 入口。
- 增加 `/api/health` 健康检查接口。
- 配置 `.env` 读取。
- 配置 PostgreSQL 连接。
- 初始化 Alembic。

### 阶段二：账号系统

- 创建 `users` 表。
- 实现密码哈希和验证。
- 实现 JWT 签发和解析。
- 完成注册、登录和当前用户接口。
- 完成普通用户与管理员权限依赖。

### 阶段三：第一项核心业务

- 确定新项目的核心业务对象。
- 设计数据库表和关联关系。
- 编写 models、schemas、crud 和 routers。
- 完成核心业务增删改查。
- 加入用户数据隔离。

### 阶段四：完善工程能力

- 增加统一响应格式。
- 增加异常处理。
- 增加分页、筛选和排序。
- 编写初始化脚本。
- 编写接口测试。
- 补充 README 和接口说明。

---

## 16. 第一版验收标准

完成以下内容后，可以认为新项目后端第一版搭建完成：

- [ ] 后端可以在本地正常启动。
- [ ] PostgreSQL 数据库连接正常。
- [ ] `/api/health` 可以正常访问。
- [ ] FastAPI Swagger 接口文档可以打开。
- [ ] Alembic 可以在空数据库中完成全部迁移。
- [ ] 用户可以注册和登录。
- [ ] JWT 身份认证正常。
- [ ] 普通用户和管理员权限区分正常。
- [ ] 核心业务表设计完成。
- [ ] 核心业务增删改查接口完成。
- [ ] 不同用户之间的数据完全隔离。
- [ ] 统一响应和异常处理生效。
- [ ] 初始化脚本可以重复执行。
- [ ] 核心接口自动化测试通过。
- [ ] `.env` 和敏感信息未提交到 Git。

---

## 17. 最终建议

新项目应复用 `exam-study-hub` 的工程结构、数据库连接、JWT 鉴权、权限校验和统一响应机制，但不复制其业务数据库表。

推荐执行方式：

```text
复用通用后端骨架
    ↓
删除“上岸计划”特有业务模块
    ↓
创建新项目独立数据库
    ↓
根据新项目功能设计业务表
    ↓
按 models → schemas → crud → routers 实现接口
    ↓
通过 Alembic 管理所有数据库变化
    ↓
使用自动化测试验证账号、权限和数据隔离
```

这样既能保持两个项目的技术风格一致，也能避免数据库结构、业务数据和后续维护互相影响。
