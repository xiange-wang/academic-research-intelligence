"""周报生成(knowledgebase 10.1/10.2):流量预算硬上限 + 覆盖声明 + 档位封顶。

评审修复:H3 预警 venue 强制归入"收录可查",不参与必读/值得关注切片;
L3 recency 时间窗过滤;L6 卡片含「论文称」引句时执行锚点门禁。
LLM 摘要为可插拔接口;接入时必须:三类陈述区分(8.2)+ 引用锚定 + 温度 0。
"""
from __future__ import annotations
from datetime import date, timedelta
from .models import ScoredPaper
from .gates import anchor_check


class Summarizer:
    """接口:实现方替换为 LLM(带 8.2 约束)。骨架返回结构化占位卡片。"""

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


def _listing_only(sp: ScoredPaper, cfg: dict) -> bool:
    """预警 venue / 可信度触底 -> 档位封顶"收录可查"(kb 6.5,评审 H3)。"""
    if sp.venue is not None and sp.venue.tier == "warning":
        return True
    return sp.credibility <= cfg.get("listing_only_credibility", 20)


def _in_window(sp: ScoredPaper, today: date, days: int) -> bool:
    if not sp.paper.pub_date:
        return False
    try:
        return date.fromisoformat(sp.paper.pub_date) >= today - timedelta(days=days)
    except ValueError:
        return False


def build(scored: list[ScoredPaper], cfg: dict, sources_stat: dict,
          summarizer: Summarizer | None = None, today: str | None = None) -> str:
    s = summarizer or Summarizer()
    t = date.fromisoformat(today) if today else date.today()
    window = [x for x in scored if not x.vetoed and _in_window(x, t, cfg["recency_window_days"])]
    eligible = [x for x in window if not _listing_only(x, cfg)]
    capped = [x for x in window if _listing_only(x, cfg)]
    ranked = sorted(eligible, key=lambda x: -x.relevance)
    cap = cfg["weekly_total_cap"]
    must = ranked[: cfg["must_read_max"]]
    worth = ranked[cfg["must_read_max"]: min(cfg["must_read_max"] + cfg["worth_attention_max"], cap)]
    overflow = max(0, len(ranked) - cap)

    def _safe_cards(items: list[ScoredPaper]) -> tuple[list[str], int]:
        cards, dropped = [], 0
        for x in items:
            c = s.card(x)
            src = x.paper.abstract or x.paper.title  # 锚点门禁(kb 15.3,评审 L6)
            if anchor_check(c, src):
                cards.append(c + "\n")
            else:
                dropped += 1
        return cards, dropped

    must_cards, d1 = _safe_cards(must)
    worth_cards, d2 = _safe_cards(worth)
    anchor_dropped = d1 + d2

    out = [f"# 研究周报 · {t.isoformat()}", "", "## 0. 本期速览",
           f"- 本期入选 {len(must_cards) + len(worth_cards)} 篇"
           f"(必读 {len(must_cards)},值得关注 {len(worth_cards)})"
           + (f";{overflow} 篇因流量预算顺延至收录可查" if overflow else "")
           + (f";{len(capped)} 篇因预警/可信度封顶仅收录可查" if capped else "")
           + (f";{anchor_dropped} 篇因锚点门禁拦截" if anchor_dropped else ""), ""]
    if len(must_cards) < cfg.get("must_read_min", 3):
        out.append(f"> 注:本期必读不足 {cfg['must_read_min']} 篇(窗口内高分论文有限,不凑数)。\n")
    out += ["## 1. 本期必读", ""] + must_cards
    out += ["## 2. 值得关注的新论文", ""] + worth_cards
    out += ["## 附录 · 本期覆盖声明",
            f"- 扫描源:{', '.join(sources_stat.get('sources', []))}",
            f"- 总采集 {sources_stat.get('total', 0)} 篇 → 去重后 {sources_stat.get('deduped', 0)}"
            f" → 时间窗内 {len(window)} → 门禁拦截 {sources_stat.get('blocked', 0)}"
            f" → 入选 {len(must_cards) + len(worth_cards)}",
            f"- 撤稿库状态:{sources_stat.get('retraction_status', '未同步(本期未做撤稿比对!)')}",
            "- 缺失 ≠ 不存在:外部评价类信号(引用语境、社媒提及)未接入,计数为 0 不代表无争议(kb 10.1)",
            "- 已知缺口:SSRN 无 API;人文学科覆盖薄弱;约 25–30% 论文无摘要走降级排序(实验2)"]
    return "\n".join(out)
