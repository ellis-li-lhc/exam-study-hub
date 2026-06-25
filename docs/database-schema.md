# 数据库表设计（exam-study-hub）

本文档整理后端（PostgreSQL）所需的数据表，依据：

- 规划文档 `adult-undergraduate-mvp-plan.md` 第 6 节数据模型
- 前端实际使用的数据：`mvp.js`、各 Pinia store 状态、题库 `docs/*.json`、英语特训数据

按业务领域分组，并标注 **v1 必需 / 后期 / 可选** 优先级。命名约定：表名小写复数下划线，主键统一 `id`，外键 `xxx_id`。

> 数据可信度约束（规划文档第 7 节）：所有招生/分数数据必须带 `year` 与来源；分数务必区分 `line_type`（省控线 / 院校线 / 专业线），避免跨年度或跨线型混用。

---

## A. 招生目录（参考数据，主要靠导入/爬取，读多写少）

| 表 | 用途 | 关键字段 | 优先级 |
| --- | --- | --- | --- |
| `provinces` | 省份 | id, code, name | v1 |
| `majors` | 专业 | id, code, name, category | v1 |
| `major_subjects` | 专业↔统考科目（1:N） | id, major_id→majors, subject_id→subjects | v1 |
| `institutions` | 院校 | id, code, name, province_id→provinces, city, duration, tuition, teaching_site, degree | v1 |
| `institution_programs` | 院校招生专业（M:N，含招生年度、是否加试） | id, institution_id→institutions, major_id→majors, year, has_extra_exam | v1 |
| `admission_scores` | 录取分数线 | id, institution_id→institutions, major_id→majors(可空), year, score, line_type, source_id→data_sources | v1 |
| `data_sources` | 数据来源与可信度 | id, source_type, url, published_at, collected_at, confidence | v1 |
| `admission_year_configs` | 参考年度切换配置（几月切下一年度） | id, cutoff_month, note | 后期 |
| `province_eligibility_rules` | 分省分年度报名资格提示 | id, province_id→provinces, year, note, source_id→data_sources | 后期 |

`line_type` 取值：`province`（省控线）/ `institution`（院校线）/ `major`（专业线）。

---

## B. 考试科目 & 题库

| 表 | 用途 | 关键字段 | 优先级 |
| --- | --- | --- | --- |
| `subjects` | 科目字典（政治/英语/高数一/高数二/大学语文/教育理论/民法） | id, name | v1 |
| `question_topics` | 知识点 | id, subject_id→subjects, name | v1 |
| `questions` | 题目 | id, topic_id→question_topics, stem, options(JSON), answer | v1 |

对应现有 `docs/*.json` 的 `topics → questions` 结构，诊断与阶段测试共用同一题库。

---

## C. 用户 & 报考档案

| 表 | 用途 | 关键字段 | 优先级 |
| --- | --- | --- | --- |
| `users` | 账号（鉴权用） | id, email, hashed_password, created_at | 后期 |
| `user_profiles` | 报考档案 | id, user_id→users, exam_year, major_id→majors, selected_institution_id→institutions, mode, weekday_hours, weekend_hours, start_date | v1 |
| `user_profile_provinces` | 档案所选省份（可多选，M:N） | profile_id→user_profiles, province_id→provinces | v1 |

v1 单用户阶段：`user_id` 可先固定或允许为空，等做鉴权再补 `users` 表与外键约束。`mode` 取值 `plan`（计划模式）/ `self`（自主模式）。

---

## D. 入学诊断

| 表 | 用途 | 关键字段 | 优先级 |
| --- | --- | --- | --- |
| `diagnostics` | 一次诊断主记录 | id, user_id→users, completed, knowledge, speed, mistake_type, correct_count, total_questions, duration_seconds, created_at | v1 |
| `diagnostic_subject_scores` | 分科结果 | id, diagnostic_id→diagnostics, subject_id→subjects, score(150 制), mastery | v1 |
| `diagnostic_answers` | 逐题作答明细 | id, diagnostic_id→diagnostics, question_id→questions, user_answer, is_correct | v1 |

对应前端 store 的 `diagnostic` 对象。`knowledgeDetails`（知识点掌握度）可由 `diagnostic_answers` 聚合得出，不必单独建表。

---

## E. 目标分（多为计算派生）

| 表 | 用途 | 关键字段 | 优先级 |
| --- | --- | --- | --- |
| `score_targets` | 目标分快照（便于留痕/审计） | id, user_id→users, reference_score, target_score, line_type_used, years_used(JSON), subject_targets(JSON), created_at | 可选 |

目标总分、分科目标当前为实时计算（参考线 + 30、按诊断掌握度分配）。若不需要历史留痕，可不落表。

---

## F. 学习计划 & 进度

| 表 | 用途 | 关键字段 | 优先级 |
| --- | --- | --- | --- |
| `study_stages` | 四阶段模板（参考数据） | id, name, weeks, description, target | v1 |
| `study_plans` | 用户学习方案 | id, user_id→users, current_stage, estimated_weeks, target_date | v1 |
| `study_tasks` | 学习任务 | id, plan_id→study_plans, subject, title, duration, type, scheduled_date, done | v1 |
| `stage_tests` | 阶段测试记录 | id, user_id→users, stage, score, accuracy, correct_count, total_questions, weak_knowledge, threshold, passed, taken_at | v1 |

`study_stages` 对应 `mvp.js` 的 `stageTemplates`；`study_tasks` 对应 `tasks`/`todayTasks`；`stage_tests` 对应 store 的 `stageTests`。

---

## G. 英语特训

### G.1 内容数据（参考数据，**可选是否入库**）

| 表 | 用途 | 关键字段 |
| --- | --- | --- |
| `vocab_words` | 3500 核心词 | id, word, phonetic, meaning, tag, letter |
| `english_items` | 造句基础 + 核心短语（category 区分） | id, category, group_key, group_name, group_short, group_desc, word, tag, meaning, example, sort_order |
| `grammar_sections` | 语法分节 | id, key, name, short |
| `grammar_points` | 语法点 | id, section_id→grammar_sections, title, explain, examples(JSON) |
| `grammar_quizzes` | 语法自测题 | id, section_id→grammar_sections, stem, options(JSON), answer |

### G.2 用户进度（**真正需要入库的部分**，用于跨设备同步）

| 表 | 用途 | 关键字段 |
| --- | --- | --- |
| `user_vocab_progress` | 3500 词掌握 | id, user_id→users, word_id→vocab_words, known |
| `user_english_progress` | 造句/短语/语法掌握 | id, user_id→users, item_type, item_key, known |

**建议**：G.1 这 5 张内容表第一版可以不入库，继续作为前端 JSON 静态资源，后端只维护 G.2 两张进度表（`item_key` 用前端现有的 `ess:组|词` / `phr:组|词` / `gra:节|序号` 字符串）。等需要后台维护词表时再把内容入库。

---

## 优先级汇总

**v1 闭环最小集（约 16 张）**：

- A 组前 7 张（provinces, majors, major_subjects, institutions, institution_programs, admission_scores, data_sources）
- B 组全部（subjects, question_topics, questions）
- C 组 `user_profiles` + `user_profile_provinces`
- D 组全部（diagnostics, diagnostic_subject_scores, diagnostic_answers）
- F 组全部（study_stages, study_plans, study_tasks, stage_tests）

**后期**：`users` 与鉴权、`admission_year_configs`、`province_eligibility_rules`、英语内容入库。

**可选**：`score_targets`（目标分快照）。

---

## 关系概览（核心外键）

```
provinces ──< institutions ──< institution_programs >── majors
                  │                                      │
                  └──< admission_scores >────────────────┘
                              │
                        data_sources

subjects ──< question_topics ──< questions
   │
   └──< major_subjects >── majors

users ──< user_profiles ──< user_profile_provinces >── provinces
  │            │
  │            ├── majors (major_id)
  │            └── institutions (selected_institution_id)
  │
  ├──< diagnostics ──< diagnostic_subject_scores >── subjects
  │         └──< diagnostic_answers >── questions
  │
  ├──< study_plans ──< study_tasks
  ├──< stage_tests
  ├──< user_vocab_progress >── vocab_words
  └──< user_english_progress
```
