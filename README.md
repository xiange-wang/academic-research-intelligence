# 学术研究情报系统 · 方法论知识库

一个面向多学科的学术论文追踪系统:用户选定研究方向,系统持续采集新论文,评估重要性与可信度,识别趋势与研究空白,生成周报 / 月报。

## 第一阶段:方法论与信息源设计

- **[knowledgebase.md](knowledgebase.md)** — 完整知识库(20 章,数据源地图 / 期刊分级 / 评分模型 / 趋势识别 / 研究空白 / 合规风险 / 技术选型 / schema 设计)
- [academic_research_system_prompt.md](academic_research_system_prompt.md) — 原始调研任务书
- **[related_solutions.md](related_solutions.md)** — 现有方案扫描与可借鉴方法(开源项目 / 商业产品方法深挖 / LLM 科研助手系统)
- [review_report.md](review_report.md) — 三视角审查报告与修改计划(事实核查 / 一致性 / 工程可实施性)
- [docs/index.html](docs/index.html) — 网页版(GitHub Pages)

## 第二阶段:MVP 骨架([mvp/](mvp/))

按知识库 v1.4 的方法论实现的可运行代码骨架(11 模块、23 项单测全过、真实数据端到端冒烟通过):

- [mvp/README.md](mvp/README.md) — 模块地图与骨架状态声明
- [mvp/BACKLOG.md](mvp/BACKLOG.md) — 骨架 → 栈 A(单用户零服务器版)补齐清单(14 件)
- [mvp/experiments/results.md](mvp/experiments/results.md) — 开工前实验数据(OpenAlex 日增量、摘要覆盖率)

技术栈选型(第 13、14 章)已于 v1.4 解冻定稿:两套推荐栈(SQLite 零服务器 / PostgreSQL+pgvector 共享湖)与无 schema 变更的迁移路径。
