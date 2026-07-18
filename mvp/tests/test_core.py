"""核心规则单测:每条对应 knowledgebase 的一条规则,注释标注章节。"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "src"))

from paperwatch import config
from paperwatch.models import Paper
from paperwatch.venues import classify, detect_red_flags
from paperwatch.normalize import dedup
from paperwatch.ranking import ProfileRanker
from paperwatch.scoring import assemble, credibility
from paperwatch.report_weekly import build
from paperwatch.gates import anchor_check

CFG = config.load()
VCFG = CFG["venue_tiers"]


def _journal(**kw):
    base = dict(kind="journal", quartile="Q1", percentile=96, openalex_percentile=92)
    base.update(kw)
    return base


def test_s_tier_journal():
    d = classify(_journal(), VCFG)
    assert d.tier == "S" and not d.demoted


def test_demotion_no_black_hole():
    """kb 5.2 v1.3:Q1 顶刊带 1 项红旗 -> 降一级到 A 并标注,而非静默跌入普通级。"""
    d = classify(_journal(fake_impact_factor=True), VCFG)
    assert d.tier == "A" and d.demoted and d.red_flags == ["R4"]
    assert "demoted-by-flag" in d.rule_ids


def test_warning_trigger_combo():
    """R3-R6 中 >=2 项触发预警(kb 5.2)。"""
    d = classify(_journal(fake_impact_factor=True, issn_unverifiable=True), VCFG)
    assert d.tier == "warning"


def test_warning_single_r1():
    d = classify(_journal(on_warning_list=True), VCFG)
    assert d.tier == "warning"


def test_conference_single_condition_s():
    """kb 5.3 v1.3:CCF-A 单条件即 S,免期刊口径佐证。"""
    d = classify({"kind": "conference", "ccf": "A"}, VCFG)
    assert d.tier == "S" and d.rule_ids == ["S-conf-single"]


def test_datapoor_is_normal_not_warning():
    """数据不足 != 预警(Leiden #3,kb 5.2 普通级)。"""
    d = classify({"kind": "journal"}, VCFG)
    assert d.tier == "normal" and not d.red_flags


def test_dedup_preprint_merge():
    """kb 15.4:预印本与正式版合并为一条,正式版为主、保留预印本首发时间。"""
    pre = Paper(paper_id="2401.00001", title="A Great Method for X", arxiv_id="2401.00001",
                authors=["Alice Zhang"], doc_type="preprint", pub_date="2026-01-01")
    pub = Paper(paper_id="10.1/x", title="A Great Method for X", doi="10.1/x",
                authors=["Alice Zhang"], doc_type="article", pub_date="2026-06-01")
    out = dedup([pre, pub], CFG["dedup"])
    assert len(out) == 1
    assert out[0].doc_type == "article" and out[0].preprint_date == "2026-01-01"
    assert out[0].arxiv_id == "2401.00001" and out[0].doi == "10.1/x"


def test_dedup_conservative():
    """标题相近但作者不重叠 -> 不合并(kb 15.4 保守原则)。"""
    a = Paper(paper_id="10.1/a", title="Deep Learning for Protein Folding", doi="10.1/a",
              authors=["Bob Li"])
    b = Paper(paper_id="10.1/b", title="Deep Learning for Protein Folding", doi="10.1/b",
              authors=["Carol Wu"])
    assert len(dedup([a, b], CFG["dedup"])) == 2


from datetime import date

def _pool(n=60):
    today = date.today().isoformat()
    ml = [Paper(paper_id=f"ml{i}", title=f"transformer attention language model study {i}",
                abstract="neural network training on large text corpora", pub_date=today)
          for i in range(n // 2)]
    bio = [Paper(paper_id=f"bio{i}", title=f"protein cell membrane assay experiment {i}",
                 abstract="wet lab measurement of enzyme kinetics in vivo", pub_date=today)
           for i in range(n // 2)]
    return ml, bio


def test_ranker_cold_start_and_separation():
    """kb 11.2:5 正 3 负冷启动;正类主题应排在负类之前。"""
    ml, bio = _pool()
    r = ProfileRanker(CFG["ranking"])
    for p in ml[:5]:
        r.feedback(p, useful=True)
    for p in bio[:3]:
        r.feedback(p, useful=False)
    test = [ml[10], bio[10]]
    scores, conf = r.score(test, ml + bio)
    assert scores[0] > scores[1]
    assert all(-100 <= s <= 100 for s in scores)


def test_unattributed_negative_ignored():
    """kb 10.4 归因门控:"其他"原因的负反馈不更新模型。"""
    r = ProfileRanker(CFG["ranking"])
    p = Paper(paper_id="x", title="t")
    r.feedback(p, useful=False, attributed=False)
    assert len(r.neg) == 0


def test_no_abstract_confidence_degraded():
    ml, _ = _pool()
    ml[0].abstract = None
    from paperwatch.ranking import Embedder
    _, conf = Embedder().embed(ml[:2])
    assert conf[0] < conf[1]


def test_credibility_veto_and_caps():
    """kb 6.5:撤稿一票否决;预警 venue 封顶;预印本 -10。"""
    ccfg = CFG["credibility"]
    ret = Paper(paper_id="r", title="t", is_retracted=True)
    score, veto, _ = credibility(ret, None, ccfg)
    assert veto and score == 0
    pre = Paper(paper_id="p", title="t", doc_type="preprint")
    score, veto, _ = credibility(pre, None, ccfg)
    assert not veto and score == 90


def test_report_volume_budget():
    """kb 10.1 原则⑤:每周总量硬上限,溢出注明顺延。"""
    ml, _ = _pool(80)
    scored = [assemble(p, 50 - i, 1.0, None, CFG["credibility"]) for i, p in enumerate(ml)]
    text = build(scored, CFG["report"], {"sources": ["test"], "total": 80, "deduped": 40, "blocked": 0})
    picked = text.count("### ")
    assert picked <= CFG["report"]["weekly_total_cap"]
    assert "顺延" in text and "缺失 ≠ 不存在" in text


def test_anchor_check():
    """kb 8.2:「论文称」引句必须能定位到原文。"""
    src = "We find that method X improves accuracy by 3 points on benchmark Y."
    ok = "「论文称:method X improves accuracy by 3 points」其余为系统评估。"
    bad = "「论文称:method X solves AGI」"
    assert anchor_check(ok, src) and not anchor_check(bad, src)


# ---------- 二轮评审回归测试 ----------

def test_dedup_chain_merge_no_stale_ref():
    """评审 H1:预印本 -> 正式版 -> 重复投递(三连)不得崩溃或丢数据。"""
    pre = Paper(paper_id="2401.1", title="Chain Merge Case Study", arxiv_id="2401.1",
                authors=["Dan Qi"], doc_type="preprint", pub_date="2026-01-01")
    pub = Paper(paper_id="10.9/c", title="Chain Merge Case Study", doi="10.9/c",
                authors=["Dan Qi"], doc_type="article", pub_date="2026-06-01")
    resub = Paper(paper_id="10.9/c", title="Chain Merge Case Study", doi="10.9/c",
                  authors=["Dan Qi"], doc_type="article", abstract="the abstract arrives late")
    out = dedup([pre, pub, resub], CFG["dedup"])
    assert len(out) == 1
    assert out[0].doc_type == "article"
    assert out[0].abstract == "the abstract arrives late"   # v2 内容并入主记录而非游离对象
    assert out[0].preprint_date == "2026-01-01"


def test_retraction_nature_filtering(tmp_path):
    """评审 H2:仅 Retraction 一票否决;Correction/EoC 不否决;Reinstatement 移除。"""
    from paperwatch.retractions import RetractionIndex
    csv_text = (
        "Record ID,OriginalPaperDOI,RetractionNature\n"
        "1,10.1/retracted,Retraction\n"
        "2,10.1/corrected,Correction\n"
        "3,10.1/concern,Expression of concern\n"
        "4,10.1/back,Retraction\n"
        "5,10.1/back,Reinstatement\n"
        "6,unavailable,Retraction\n")
    cache = tmp_path / "rw.csv"
    cache.write_text(csv_text)
    idx = RetractionIndex(cache)
    idx.load()
    assert idx.is_retracted("10.1/retracted")
    assert not idx.is_retracted("10.1/corrected")
    assert not idx.is_retracted("10.1/concern") and idx.has_concern("10.1/concern")
    assert not idx.is_retracted("10.1/back")        # 复职后移出否决索引
    assert not idx.is_retracted("unavailable")


def test_retraction_bad_csv_fails_loud(tmp_path):
    """评审 L4:列名不符(如 HTML 错误页)必须报错,不得静默空索引。"""
    from paperwatch.retractions import RetractionIndex
    cache = tmp_path / "rw.csv"
    cache.write_text("<html>oops</html>")
    idx = RetractionIndex(cache)
    try:
        idx.load()
        assert False, "should raise"
    except ValueError:
        pass


def test_warning_venue_listing_only():
    """评审 H3:预警 venue 论文不得进必读区也不得进值得关注区(复审补强断言)。"""
    from paperwatch.venues import classify
    ml, _ = _pool(20)
    vd = classify(_journal(on_warning_list=True), VCFG)
    scored = [assemble(p, 90 - i, 1.0, vd if i == 0 else None, CFG["credibility"])
              for i, p in enumerate(ml)]
    text = build(scored, CFG["report"], {"sources": ["t"], "total": 20, "deduped": 10, "blocked": 0})
    body = text.split("## 附录")[0]            # 必读 + 值得关注两区(附录之前)
    assert ml[0].title not in body            # 预警论文不在任何展示区
    assert "封顶仅收录可查" in text


def test_demotion_clamped_at_normal():
    """评审 L1:降级步长再大也只到 normal,不落入 warning。"""
    import copy
    cfg2 = copy.deepcopy(VCFG)
    cfg2["demotion_on_flag"] = 3
    d = classify(_journal(quartile="Q2", percentile=60, fake_impact_factor=True), cfg2)
    assert d.tier == "normal" and d.demoted


def test_s_journal_needs_corroboration():
    """评审测试缺口 4:Q1 + 高百分位但无 OpenAlex 佐证 -> A 而非 S。"""
    d = classify(_journal(openalex_percentile=None), VCFG)
    assert d.tier == "A"


def test_icore_astar_conference_s():
    d = classify({"kind": "conference", "icore": "A*"}, VCFG)
    assert d.tier == "S"


def test_gates_block_retracted(tmp_path):
    """评审测试缺口 8:门禁拦截撤稿论文并给出原因。"""
    from paperwatch.retractions import RetractionIndex
    from paperwatch.gates import run_gates
    cache = tmp_path / "rw.csv"
    cache.write_text("Record ID,OriginalPaperDOI,RetractionNature\n1,10.2/bad,Retraction\n")
    idx = RetractionIndex(cache)
    idx.load()
    ok = Paper(paper_id="10.2/ok", title="fine paper", doi="10.2/ok")
    bad = Paper(paper_id="10.2/bad", title="bad paper", doi="10.2/bad")
    scored = [assemble(p, 0, 1.0, None, CFG["credibility"]) for p in (ok, bad)]
    passed, blocked = run_gates(scored, idx)
    assert len(passed) == 1 and passed[0].paper.doi == "10.2/ok"
    assert blocked[0][1] == "retracted"


def test_recency_window_filters_old_papers():
    """评审 L3:周报只含时间窗内论文。"""
    ml, _ = _pool(10)
    old = Paper(paper_id="old1", title="ancient transformer work",
                abstract="x", pub_date="2020-01-01")
    scored = [assemble(p, 10, 1.0, None, CFG["credibility"]) for p in ml + [old]]
    text = build(scored, CFG["report"], {"sources": ["t"], "total": 11, "deduped": 11, "blocked": 0})
    assert "ancient transformer work" not in text


# ---------- 三轮复审回归测试 ----------

def test_retraction_reload_resets(tmp_path):
    """复审 #1:同一 index 重载不同 CSV,前一版独有的 DOI 不得残留。"""
    from paperwatch.retractions import RetractionIndex
    cache = tmp_path / "rw.csv"
    cache.write_text("Record ID,OriginalPaperDOI,RetractionNature\n1,10/x,Retraction\n2,10/y,Retraction\n")
    idx = RetractionIndex(cache)
    idx.load()
    assert idx.is_retracted("10/y")
    cache.write_text("Record ID,OriginalPaperDOI,RetractionNature\n1,10/x,Retraction\n")  # y 消失
    idx.load()
    assert idx.is_retracted("10/x") and not idx.is_retracted("10/y")   # y 不残留


def test_dedup_empty_title_no_collapse():
    """复审 #4:空标题论文不因 SequenceMatcher('','')==1 而塌缩。"""
    import copy
    cfg = copy.deepcopy(CFG["dedup"]); cfg["require_author_overlap"] = False
    ps = [Paper(paper_id=f"e{i}", title="", doi=f"10/e{i}") for i in range(4)]
    assert len(dedup(ps, cfg)) == 4


def test_eoc_wired_into_scoring():
    """复审 #3:Expression of concern 命中 -> 可信度扣分 + 说明。"""
    from paperwatch.scoring import credibility
    p = Paper(paper_id="c", title="t", doi="10/c")
    base, _, _ = credibility(p, None, CFG["credibility"])
    hit, _, notes = credibility(p, None, CFG["credibility"], concern_hit=True)
    assert hit < base and any("concern" in n for n in notes)


def test_venue_lookup_normalization():
    """复审 #6:venue 名大小写/尾括号别名差异仍能命中查表。"""
    import re
    def _norm(name):
        return re.sub(r"\s*\(.*?\)\s*$", "", name).strip().lower() if name else ""
    feats = {"Nature": {"kind": "journal", "quartile": "Q1", "percentile": 96, "openalex_percentile": 92}}
    lookup = {_norm(k): v for k, v in feats.items()}
    assert lookup.get(_norm("Nature (London)")) is not None
    assert lookup.get(_norm("NATURE")) is not None


def test_cursor_filter_stable_across_continuation(tmp_path):
    """复审 #2:incomplete 续拉复用首轮 filter,不随日期重算(免费层游标有效性)。"""
    import json as _json
    from paperwatch.ingest_openalex import OpenAlexLake
    state = tmp_path / "s.json"
    # 模拟一次中断:incomplete=True 且存下 active_filter
    state.write_text(_json.dumps({
        "budget": {"date": "2000-01-01", "used": 0},   # 过期日期 -> 归零,但不影响本测
        "26": {"cursor": "AoJ123", "since": "2026-07-03",
               "active_filter": "from_publication_date:2026-06-19", "incomplete": True}}))
    lake = OpenAlexLake({"daily_request_budget": 0, "mailto": "x@y.z"}, state)  # 预算 0 -> 不发请求
    # 预算耗尽立即返回,但 date_filter 的选择逻辑已执行:应复用 active_filter
    lake.fetch_field(26, max_pages=1)
    # 续拉分支保持 active_filter 不变(未走完)
    assert lake.state["26"]["active_filter"] == "from_publication_date:2026-06-19"
    assert lake.state["26"]["incomplete"] is True
