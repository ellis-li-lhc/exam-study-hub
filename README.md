# 上岸计划 · 成人高考专升本个人备考系统

面向**成人高考专升本**考生的个人备考工具,把「选省份/专业 → 看院校 → 入学诊断 → 定目标分 → 生成学习计划 → 阶段测试与动态纠偏」串成一条完整闭环。

> 当前版本为**江苏 MVP**:仅覆盖江苏省,院校与投档线为江苏省教育考试院公开数据。河南等省份待数据可得后接入。

---

## ✨ 核心特性

- **报考档案**:按省 → 市 → 专业逐级选择;专业自动映射到报考科类与统考科目。
- **专业与院校**:基于江苏省教育考试院 2025 年真实投档线,按科类反查招生院校,标注学制、学费、所在市与数据来源/可信度。
- **入学诊断**:从后端真实题库(7 科 / 60 知识点 / 239 题)按科目组织单选题,自动计算分科预估分、知识点掌握度、薄弱项。
- **目标分分析**:取近三年较高投档线 + 30 分安全空间;结合诊断掌握度做分科目标分配,可信度按数据真实性动态展示。
- **学习路线**:按诊断结果与考试日期自动生成四阶段计划、每日任务与达标里程碑;支持计划模式 / 自主模式。
- **阶段测试与动态纠偏**:测试答错的知识点自动进入复习队列并重排到当日任务,落后时阶段自动压缩。
- **账号与云端同步**:JWT 登录注册,报考档案 / 诊断 / 进度同步到云端,换设备不丢。
- **管理员后台**:用户列表、角色管理、查看用户填报信息、重置密码(密码仅哈希存储,不可查看明文)。

## 🧭 主流程

```
登录 / 注册
  → 报考档案(省 / 市 / 专业 / 学习模式)
  → 专业与院校(真实江苏投档线)
  → 入学诊断(真实题库自动判分)
  → 目标分分析(参考线 + 30 分)
  → 学习路线(四阶段 + 每日任务)
  → 阶段测试 → 动态纠偏 → 学习进度
```

## 🛠 技术栈

**前端** `exam-study-hub-client`
- Vue 3 + Vite 5 + Vue Router 4 + Pinia
- Element Plus(UI)、ECharts、Axios(含请求/响应拦截器)

**后端** `exam-study-hub-server`
- FastAPI + SQLAlchemy 2.0 + Alembic(迁移)
- PostgreSQL
- JWT(PyJWT)鉴权 + bcrypt 密码哈希

## 📂 仓库结构(monorepo)

```
exam-study-hub/
├── docs/                     # 项目规划与数据库设计文档
├── exam-study-hub-client/    # 前端(Vue 3 + Vite)
│   ├── src/views/            # 页面:报考档案/院校/诊断/目标/计划/进度/英语特训/用户管理
│   ├── src/stores/           # Pinia:application / auth / 进度
│   ├── src/api/              # 按资源拆分的接口封装
│   └── src/data/             # 专业-科类、省份等静态数据
└── exam-study-hub-server/    # 后端(FastAPI)
    ├── app/models/           # ORM 模型
    ├── app/routers/          # 路由:auth/majors/provinces/institutions/questions/state/admin
    ├── app/crud/             # 数据访问层
    ├── alembic/              # 数据库迁移
    └── scripts/              # 数据抓取与入库脚本
```

## 🚀 快速开始

### 1. 后端

```bash
cd exam-study-hub-server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # 配置 DATABASE_URL、SECRET_KEY

createdb exam_study           # 创建 PostgreSQL 数据库
alembic upgrade head          # 建表
python -m scripts.seed            # 省份 / 专业 / 院校 / 投档线 / 城市
python -m scripts.seed_questions  # 诊断题库

uvicorn app.main:app --reload --port 8000
```

API 文档:http://localhost:8000/docs

### 2. 前端

```bash
cd exam-study-hub-client
npm install
npm run dev                   # http://localhost:5173 ，/api 代理到 8000
```

## 🗄 数据库表

`provinces` · `majors` · `major_subjects` · `institutions` · `admission_scores` · `question_topics` · `questions` · `users` · `user_states`

## 📌 数据真实性与免责声明

- 院校与投档线来自**江苏省教育考试院**公开数据(2025 年院校投档线),院校详情可追溯到原始文件链接。
- 成人高考**不公布逐专业录取线**,逐院校招生专业目录仅在报名期、网上报名系统内开放,**不可公开抓取**。因此院校匹配粒度止于**科类**;专业归属、是否开设、统考科目**以院校当年招生计划为准**。
- 城市为院校校本部所在市,实际就读以教学点为准。
- 本系统仅辅助个人决策与备考,**不构成录取承诺**,不替代省教育考试院及院校发布的正式招生政策。

## 🧱 当前局限 & 后续规划

- [ ] 更多省份数据(待可得的官方来源)
- [ ] 计划与题库深度:每日任务质量、题量扩充、错题本

## 📄 使用许可

本项目仅供**个人学习、研究与非商业性备考**使用。

- ✅ 允许:个人自用、学习参考、非营利的研究与交流。
- ❌ 禁止:任何形式的**商业用途**,包括但不限于售卖、付费服务、商业培训、广告变现,或将本项目(及其代码、数据)整体或部分用于盈利。
- 如需商业授权,请先联系作者获得书面许可。
- 项目中的招生与分数数据版权归原发布机构(如江苏省教育考试院及各院校)所有,本项目仅作个人备考整理之用。

> 在未获授权的情况下,使用者需自行承担因商业使用产生的一切责任。

---

仅用于个人学习与备考用途,禁止商业使用。
