"""准入与呈现评分(knowledgebase 6.4/6.5 v1.3 分工)。

排序 = ranking.ProfileRanker 的 LR 分;本模块负责:可信度扣分制(独立公式)、
撤稿一票否决(公式外覆盖)、venue 档位封顶。输出 ScoredPaper 供报告分档。
"""
from __future__ import annotations
from .models import Paper, ScoredPaper, VenueDecision


def credibility(paper: Paper, venue: VenueDecision | None, cfg: dict,
                pubpeer_hit: bool = False, concern_hit: bool = False
                ) -> tuple[float, bool, list[str]]:
    """返回 (可信度分, 是否一票否决, 说明)。扣分制:满分起步按红旗扣减(kb 6.4)。"""
    notes: list[str] = []
    if paper.is_retracted:
        return 0.0, True, ["retracted: composite score vetoed (kb 6.5)"]
    score = float(cfg["start"])
    if venue and venue.tier == "warning":
        score = min(score, float(cfg["warning_venue_cap"]))
        notes.append("warning venue: credibility capped, listing-only tier (kb 6.5)")
    if concern_hit:   # Expression of concern(评审复审 #3:EoC 接入扣分制)
        score += cfg.get("expression_of_concern", -20)
        notes.append(f"expression of concern: {cfg.get('expression_of_concern', -20)}, route to human review")
    if pubpeer_hit:
        score += cfg["pubpeer_hit"]
        notes.append("PubPeer hit: -30, route to human review")
    if paper.doc_type == "preprint":
        score += cfg["preprint"]
        notes.append("preprint (not peer-reviewed): -10")
    return max(score, 0.0), False, notes


def assemble(paper: Paper, relevance: float, conf: float,
             venue: VenueDecision | None, cfg: dict,
             pubpeer_hit: bool = False, concern_hit: bool = False) -> ScoredPaper:
    cred, vetoed, notes = credibility(paper, venue, cfg,
                                      pubpeer_hit=pubpeer_hit, concern_hit=concern_hit)
    if paper.abstract is None:
        notes.append("no abstract: title-only embedding, confidence lowered (exp2)")
    return ScoredPaper(paper=paper, relevance=relevance, credibility=cred,
                       venue=venue, confidence=conf, vetoed=vetoed, notes=notes)
