# paperwatch — 学术研究情报系统 MVP 骨架

按 `../knowledgebase.md` v1.4 的方法论实现的最小可行产品骨架。每个模块头部注释标注其对应的知识库章节。

## ⚠ 骨架状态声明(2026-07-17 修复轮后)

- **存储层为临时形态**:当前 JSONL append 存储;定稿为 kb 第 14 章 SQLite schema(补齐清单第 1 件)。**湖文件不进 git**(kb 13.1:R2 / Releases)。
- **门禁部分接线**:`anchor_check` 已接入报告发布路径(拦截「论文称」引句无法定位的卡片);撤稿库缺失已 fail-loud(须显式 `--allow-stale-retractions`)。**仍缺**:链接可达性默认关闭(BACKLOG #8)、撤稿索引时新性检查未做。
- **venue 引擎装载器未实现**:`classify()` 规则已测,CLI 已预留 `--venues` JSON 查表接口;但 SCImago/CCF/ICORE/DOAJ 名单的装载器(BACKLOG #5)未实现,缺省时 venue 信号不参与。
- **嵌入为 Hashing 占位**:生产嵌入待实验 7 三方基准(Qwen3-0.6B / gte-large / SPECTER2)裁决。
- 完整"骨架 → 栈 A 补齐清单"(14 件,关键路径约 8–10 人天)见 [`BACKLOG.md`](BACKLOG.md)。

## 模块地图(对应 knowledgebase 章节)

| 模块 | 职责 | 依据章节 |
|---|---|---|
| `ingest_openalex.py` | 共享摄入湖:按学科增量拉取(游标持久化 + 预算护栏) | 2.3、3.1.1、12.1 |
| `ingest_arxiv.py` | arXiv 增量(1 req/3s 限速、submittedDate 游标) | 3.1.4 |
| `normalize.py` | 去重(DOI/arXiv 精确 + 保守模糊)与预印本↔正式版合并 | 15.4 |
| `retractions.py` | Retraction Watch CSV 每日同步与红旗 | 15.1 |
| `venues.py` | 五级分级规则引擎(R1–R7 红旗、降级规则、会议单条件路径) | 4.3、5.2、5.3 |
| `ranking.py` | Scholar Inbox 配方:冻结嵌入 + 每档案逻辑回归 + 随机负例 | 11.2、6.5 分工 |
| `scoring.py` | 准入与呈现:可信度扣分制 + venue/时效信号 | 6.4、6.5 |
| `report_weekly.py` | 周报生成(模板 + 流量预算 ≤20 + 覆盖声明) | 10.1、10.2 |
| `gates.py` | 质量门禁(一票否决):链接可达、撤稿比对、锚点存在性 | 15.3 |
| `cli.py` | `ingest` / `sync-retractions` / `report` 命令 | 12.3 节奏 |

## 设计初值都在配置里

`config/default.yaml` 承载全部"设计初值"(评分权重、扣分档位、流量预算、阈值)——knowledgebase 反复强调这些是待回测校准的先验,**不硬编码**。

## 实验数据(2026-07-17 实测)

见 `experiments/results.md`:OpenAlex 日增量 1.8–4.9 万篇/天;摘要覆盖率 CS 77.3% / 医学 70.7% / 数学 74.8%(→ 无摘要降级路径已实现:仅标题嵌入 + 置信度降级)。

## 运行

```bash
cd mvp && pip install -e . && python -m paperwatch.cli --help
python -m pytest tests/ -q
```

LLM 摘要环节为可插拔接口(`report_weekly.Summarizer`),骨架阶段输出结构化占位卡片;接入模型时必须实现三类陈述区分与引用锚定(knowledgebase 8.2,由 `gates.anchor_check` 强制)。
