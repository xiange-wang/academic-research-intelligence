"""周报生成(knowledgebase 10.1/10.2):流量预算硬上限 + 覆盖声明。

LLM 摘要为可插拔接口;骨架输出结构化占位卡片。接入 LLM 时必须:
三类陈述区分(8.2)+ 引用锚定(gates.anchor_check)+ 温度 0 + 结构化抽取。
"""
from __future__ import annotations
from datetime import date
from .models import ScoredPaper


class Summarizer:
    """接口:实现方替换为 LLM(带 8.2 约束)。骨架返回占位。"""

    def card(self, sp: ScoredPaper) -> str:
        p = sp.paper
        lines = [
            f"### {p.title}",
            f"- 作者:{', '.join(p.authors[:5]) or '未知'}{' 等' if len(p.authors) > 5 else ''}",
            f"- 来源:{p.venue or '未知'}"
            + (f"(分级 {sp.venue.tier},规则 {'/'.join(sp.venue.rule_ids)})" if sp.venue else ""),
            f"- 日期:{p.pub_date or '未知'}"
            + (f"(预印本首发 {p.preprint_date})" if p.preprint_date else ""),
            f"- 链接:https://doi.org/{p.doi}" if p.doi else f"- ID:{p.paper_id}",
            f"- 「系统评估」相关性 {sp.relevance:+.0f} / 可信度 {sp.credibility:.0f}"
            + (f"(置信度 {sp.confidence:.0%})" if sp.confidence < 1 else ""),
        ]
        lines += [f"- ⚠ {n}" for n in sp.notes]
        return "\n".join(lines)


def build(scored: list[ScoredPaper], cfg: dict, sources_stat: dict,
          summarizer: Summarizer | None = None, today: str | None = None) -> str:
    """按相关性排序分档;总量硬上限(kb 10.1 原则⑤)。"""
    s = summarizer or Summarizer()
    today = today or date.today().isoformat()
    ranked = sorted((x for x in scored if not x.vetoed), key=lambda x: -x.relevance)
    cap = cfg["weekly_total_cap"]
    must = ranked[: cfg["must_read_max"]]
    worth = ranked[cfg["must_read_max"]: min(cfg["must_read_max"] + cfg["worth_attention_max"], cap)]
    overflow = max(0, len(ranked) - cap)

    out = [f"# 研究周报 · {today}", "", "## 0. 本期速览",
           f"- 本期入选 {len(must) + len(worth)} 篇(必读 {len(must)},值得关注 {len(worth)})"
           + (f";{overflow} 篇因流量预算顺延至收录可查" if overflow else ""), ""]
    out += ["## 1. 本期必读", ""] + [s.card(x) + "\n" for x in must]
    out += ["## 2. 值得关注的新论文", ""] + [s.card(x) + "\n" for x in worth]
    out += ["## 附录 · 本期覆盖声明",
            f"- 扫描源:{', '.join(sources_stat.get('sources', []))}",
            f"- 总采集 {sources_stat.get('total', 0)} 篇 → 去重后 {sources_stat.get('deduped', 0)}"
            f" → 门禁拦截 {sources_stat.get('blocked', 0)} → 入选 {len(must) + len(worth)}",
            "- 缺失 ≠ 不存在:外部评价类信号(引用语境、社媒提及)未接入,计数为 0 不代表无争议(kb 10.1)",
            "- 已知缺口:SSRN 无 API;人文学科覆盖薄弱;约 25–30% 论文无摘要走降级排序(实验2)"]
    return "\n".join(out)
