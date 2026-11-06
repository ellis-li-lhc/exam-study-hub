# 湖南成人专升本数据

当前在本地系统接入61所院校：56校有2026专业目录，另外5校只有2025历史科类征集记录，不作为当前专业目标。省份指“在湖南招生”，包括省外院校；城市是校本部所在地，不能当作具体专业教学点。

| 数据 | 年份 | 条数 | 口径 |
| --- | --- | ---: | --- |
| 专升本专业目录 | 2026 | 677 | 56所院校，涵盖非脱产和原文列出的脱产专业 |
| 普通统考省控线 | 2024、2025 | 16 | 每年8个科类，独立于院校录取线 |
| 第一次科类征集 | 2025 | 124 | 6853人，只到院校和科类 |
| 第二次科类征集 | 2025 | 114 | 2404人，只到院校和科类 |

主要来源为[湖南日报2026年8月25日第7版](https://epaper.voc.com.cn/hnrb/html/2026-08/25/content_1798424.htm?div=-1)、[第8版](https://epaper.voc.com.cn/hnrb/html/2026-08/25/content_1798425.htm?div=-1)、[第9版](https://epaper.voc.com.cn/hnrb/html/2026-08/25/content_1798426.htm?div=-1)的省级统一招生专业目录，以及湖南省教育考试院发布的省控线与两次征集公告。原始页面、逐文件URL和SHA-256见 `sources/hunan/`、`hunan-manifest.json`。

专业目录不是人数计划，未公布人数、学制、学费、外语语种或具体专业教学点均保留null；不存在院校实际录取线，不以省控线代替。两轮征集余缺人数不能相加为实际录取总人数，也不能分摊给具体专业。没有2027目录，2026资料仅作2027备考历史参考。

院校使用来源中的5位招生代码，在省份内唯一。按代码关联跨年记录，2025“湖南理工学院”与2026“湖南理工大学”保持同一院校身份；原始旧校名在征集记录中保留。普通高校城市按教育部2026学校名单代码核验；不在普通高校名单的成人高校按省级目录地址核验。原始专业代码保留，续行跨段专业不会混到上一院校。两轮征集按年度、院校、科类、学习形式和轮次区分。

目录写入现有 `admission_plans`，省控线写入 `province_control_scores`；科类征集存放于 `institutions.supplemental_data.category_collection_plans`，通过独立API字段和页面折叠区域展示，不新增表。仅专业名称及科类均匹配现有备考课程的院校专业可作为学习目标，其余专业保留作来源资料。

在后端目录执行：

```sh
.venv/bin/python -m scripts.scrape_hunan_jiangxi # 使用存档重新解析；--refresh重新下载
.venv/bin/python -m scripts.seed_hunan_jiangxi # 两省事务导入，可重复运行
.venv/bin/python -m scripts.validate_data
.venv/bin/python -m unittest tests.test_hunan_jiangxi
```

主入口 `python -m scripts.seed` 也会导入两省。这批数据尚未推送部署至远程生产环境。
