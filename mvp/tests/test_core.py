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


def _pool(n=60):
    ml = [Paper(paper_id=f"ml{i}", title=f"transformer attention language model study {i}",
                abstract="neural network training on large text corpora") for i in range(n // 2)]
    bio = [Paper(paper_id=f"bio{i}", title=f"protein cell membrane assay experiment {i}",
                 abstract="wet lab measurement of enzyme kinetics in vivo") for i in range(n // 2)]
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
