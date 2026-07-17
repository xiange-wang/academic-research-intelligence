"""五级 venue 分级规则引擎。依据 knowledgebase 4.3(R1–R7 唯一红旗表)、5.2、5.3(v1.3)。

判定语义:
- 预警触发:R1|R2|R7 任一,或 R3–R6 中 >=2 项。
- S/A 排除:任何 1 项红旗排除 S/A,并触发降级规则。
- 降级规则(修复"掉级黑洞"):有红旗未达预警 -> 按无红旗规则定级后降一级并标注红旗 ID。
- 会议路径:CCF-A / ICORE A* 单条件即 S(免期刊口径佐证)。
"""
from __future__ import annotations
from datetime import date
from .models import VenueDecision

TIERS = ["S", "A", "B", "normal", "warning"]
_WARNING_SINGLE = {"R1", "R2", "R7"}
_WARNING_COMBO = {"R3", "R4", "R5", "R6"}


def detect_red_flags(v: dict, cfg: dict) -> list[str]:
    """v: venue 特征 dict。返回命中的红旗 ID(kb 4.3 唯一清单)。"""
    flags = []
    if v.get("on_warning_list") or v.get("jcr_suppressed"):
        flags.append("R1")
    if v.get("doaj_removed_misconduct") or v.get("in_cabells") or v.get("in_bealls_no_offset"):
        flags.append("R2")
    growth, count = v.get("yoy_growth", 0.0), v.get("annual_count", 0)
    if growth > cfg["red_flag_growth_ratio"] and count > cfg["red_flag_growth_abs"]:
        flags.append("R3")
    if v.get("fake_impact_factor"):
        flags.append("R4")
    if v.get("issn_unverifiable"):
        flags.append("R5")
    if v.get("is_oa") and not v.get("in_doaj") and not v.get("publisher_cope_oaspa"):
        flags.append("R6")
    if v.get("hijacked"):
        flags.append("R7")
    return flags


def _warning_triggered(flags: list[str]) -> bool:
    if any(f in _WARNING_SINGLE for f in flags):
        return True
    return len([f for f in flags if f in _WARNING_COMBO]) >= 2


def _base_tier(v: dict, cfg: dict) -> tuple[str, list[str]]:
    """无红旗前提下的定级(5.2 期刊路径 / 会议路径 / B / normal)。"""
    rules: list[str] = []
    if v.get("kind") == "conference":
        if v.get("ccf") == "A" or v.get("icore") == "A*":
            return "S", ["S-conf-single"]
        if v.get("ccf") == "B" or v.get("icore") == "A":
            return "A", ["A-conf"]
        if v.get("ccf") == "C" or v.get("icore") == "B":
            return "B", ["B-conf"]
        if v.get("dblp_indexed") or v.get("icore") == "C":
            return "normal", ["normal-conf"]
        return "normal", ["normal-conf-datapoor"]  # 数据不足 != 预警(Leiden #3)
    pct = v.get("percentile")            # 学科内百分位(kb 5.2 学科体系裁决)
    q = v.get("quartile")                # JCR 或 SCImago
    corr = v.get("openalex_percentile")  # 独立佐证
    if q == "Q1" and pct is not None and pct >= cfg["s_percentile"] \
            and corr is not None and corr >= cfg["s_corroboration_percentile"]:
        return "S", ["S-journal"]
    if q == "Q1" or (pct is not None and pct >= cfg["a_percentile_low"]):
        return "A", ["A-journal"]
    if q == "Q2" or (pct is not None and pct >= cfg["b_percentile_low"]):
        return "B", ["B-journal"]
    if v.get("indexed_scopus_wos_doaj") or v.get("norwegian_level", 0) >= 1:
        return "normal", ["normal-indexed"]
    return "normal", ["normal-datapoor"]


def classify(v: dict, cfg: dict, snapshot: str | None = None) -> VenueDecision:
    flags = detect_red_flags(v, cfg)
    snapshot = snapshot or date.today().isoformat()
    if _warning_triggered(flags):
        return VenueDecision("warning", ["warning-trigger"], flags, False, v, snapshot)
    tier, rules = _base_tier(v, cfg)
    demoted = False
    if flags and tier in ("S", "A", "B"):   # v1.3 降级规则:显式降一级,不静默跌底
        tier = TIERS[TIERS.index(tier) + cfg.get("demotion_on_flag", 1)]
        rules.append("demoted-by-flag")
        demoted = True
    return VenueDecision(tier, rules, flags, demoted, v, snapshot)
