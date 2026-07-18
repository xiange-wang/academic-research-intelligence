# 骨架 → 栈 A 补齐清单(架构评审 2026-07-17,按依赖顺序)

关键路径 1→2→4→6→7→9→12 约 8–10 人天;全量(含 5/8/10/11)约 13–16 人天到栈 A 可日常运转。

> **已完成子项(修复轮 2026-07-17,commit 73cac0e)**:#1 的 dedup stale 引用已修;#2 的双路径游标持久化 + 跨进程预算 + 全字段保留已实现;#7 的 recency_window 过滤已做;#8 的 anchor_check 接线与撤稿库缺失 fail-loud 已做。下表"内容"列已剔除这些,只留真实剩余工作。

| 序 | 工件 | 内容 | 工作量 | 依赖 |
|---|---|---|---|---|
| 1 | SQLite 存储层 | kb 14 章 schema(七实体+三边表+档案/任务状态表),SQLAlchemy 双方言,JSONL 迁移脚本;修 dedup stale 引用 | 1.5–2 天 | — |
| 2 | 采集加固 | 双路径游标已实现(Premium 用 `from_created_date`;免费层 `from_publication_date`+14 天回看——`from_created_date` 实测为 Premium 限定,免费 key 不解锁)、全字段/分页落盘已完成。**剩余**:接线 arXiv 到 CLI、申请免费 key 入 GHA secret | 0.5 天 | 1 |
| 3 | FTS5 + 检索薄模块 | 标题+自产摘要 FTS;封装 FTS5→tsvector 唯一适配点 | 0.5–1 天 | 1 |
| 4 | 真嵌入 + 实验 7 | sentence-transformers(model_version 必存)、sqlite-vec 落库;三方基准(Qwen3-0.6B/gte-large/SPECTER2,50–100 篇标注)裁决默认 | 1.5–2 天 | 1,3 |
| 5 | venue 数据装载器 | SCImago CSV/CCF/ICORE/DOAJ/预警名单 → 特征 dict + 快照日期,接入 CLI | 1.5–2 天 | 1(与 4 并行) |
| 6 | 种子导入与档案层 | 白名单例外①按 id 一次性拉种子;符号层召回并联(kb 11.2) | 1 天 | 2,4 |
| 7 | 周窗口 + 报告持久化 | recency_window 过滤;不可变快照表 + 报告—论文(卡片版本)索引 | 0.5–1 天 | 1 |
| 8 | 门禁实装 | 链接检查开启(HEAD 失败回退 GET)、撤稿索引时新性 fail-loud、anchor_check 接入发布路径 | 0.5 天 | 7 |
| 9 | LLM 摘要实装 | 裸 SDK + structured output(Pydantic 强制锚点/三类陈述)+ 过度概括抽检 | 1.5–2 天 | 8 |
| 10 | Hugo + GitHub Pages | 周报模板渲染、发布即 git 提交(与 7 双落点) | 0.5–1 天 | 7 |
| 11 | Resend 邮件 + sender 抽象 | sender 接口(SES 预留);发他人前需验证自有域名(~$10/年) | 0.5 天 | 10 |
| 12 | GHA workflows | 每日 ingest/撤稿同步 + 每周 report;模型缓存(actions/cache,固定 revision)、DB 经 R2/Releases 同步、keepalive、失败告警 | 1.5–2 天 | 2,4,10 |
| 13 | GROBID + Docling | 仅入选论文;abstract-only 卡片可先行 | 1.5–2 天 | 9(可推迟) |
| 14 | DuckDB 季度 snapshot 批处理 | 官方 Parquet 下载 + 分位数首算(实验 5/8) | 2–3 天 | 独立并行(可推迟) |

**并行项**:实验 3(端到端成本表,程序性欠账);实验 1 主体——先验证 `from_updated_date` 是否同为 Premium 限定(`from_created_date` 已确认是);若是,引用刷新只能走季度 snapshot,实验改为"验证结论"而非"测流量"。

**开工前已钉死的三件事**(v1.4 已写入 knowledgebase):存储层口径(JSONL=临时,SQLite=定稿)、嵌入口径(实验 7 三方基准)、湖文件落点(R2/Releases,不进 git)。
