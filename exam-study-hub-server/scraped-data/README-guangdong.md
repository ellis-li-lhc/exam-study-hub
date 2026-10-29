# 广东成人高考补充资料

资料采集于2026-10-22，接入于2026-10-23。范围限定为本地已收录的79所广东招生院校及746条2025年专升本主批次计划，未扩充专业主数据或推测缺失字段。

## 已接入

- `guangdong-adult-scores.json`：2025年199条第一志愿科目组投档线；`guangdong-adult-scores-history.json`：2023年184条、2024年190条，共374条历史线。
- `guangdong-adult-control-scores.json`：2025年9条按科类展开的省控线；`guangdong-adult-control-scores-history.json`：2023—2024年18条。
- `guangdong-adult-program-plan-2025.json`：746条主批次专业计划。
- `guangdong-adult-collection-plan-2025.json`：95条征集计划，保留教学点、学习形式、收费原文、计费口径和来源。80条为每学年收费，8条为总学费，7条未公布明确金额。
- `guangdong-institution-supplements-2025.json`：31所院校的52条官方资料来源及12条已核验学制/收费说明。
- `pending/guangdong/`：逐校覆盖、专业映射和待核验表格。此目录不参与seed。

运行 `alembic upgrade head` 后执行 `python -m scripts.seed_guangdong_supplements`，即可在事务内导入补充数据；重复运行不会重复插入。完整的 `python -m scripts.seed` 也会导入这些资料。使用院校代码、年份、专业名称及科目组关联，不依赖采集环境的数据库ID。

## 使用口径

1. 征集计划与主批次分别保存，人数和教学点不相互覆盖。第一批六位专业代码与征集四位院校专业代码保留各自原值。
2. `tuition_unit=per_academic_year` 表示每学年收费，`total` 表示总学费；数值未知时保留空值和原文，不自行换算。
3. 广东103组包含理工和经管，参考线按真实专业计划中的科目组匹配；考试科目仍由具体专业决定。
4. 学制、最长修业年限、最快申请毕业时间不混用。分专业学制只用于对应专业，缺少依据时显示“暂未获取”。
5. 只有 `review_status=verified_text` 的事实用于学制展示；图片识别和存在层次歧义的表格不用于自动填充。来源目录单独标注待核验。
6. 现有专业主数据仍为66个。广东计划中的149个专业名称只有57个与其匹配；其余92个保留在原始计划及待核验清单中，不自动补建考试科目或题库。

官方来源包括广东省教育考试院历年投档及省控线文件、2025年征集计划，以及各院校继续教育官网。每条记录保留原文URL；可导入文件的哈希与记录数见 `guangdong-supplement-manifest.json`。
