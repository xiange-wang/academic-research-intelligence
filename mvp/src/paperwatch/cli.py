"""CLI:ingest / sync-retractions / report(节奏见 knowledgebase 12.3:日采集、周报告)。"""
from __future__ import annotations
import argparse, json, pathlib, sys
from . import config
from .models import Paper
from .ingest_openalex import OpenAlexLake
from .normalize import dedup
from .retractions import RetractionIndex
from .report_weekly import build
from .ranking import ProfileRanker
from .scoring import assemble
from .venues import classify
from .gates import run_gates


def _load_venue_features(path: pathlib.Path | None) -> dict:
    """venue 名称 -> 特征 dict(SCImago/CCF/ICORE 装载器产物;骨架接受 JSON 查表)。"""
    if path and path.exists():
        return json.loads(path.read_text())
    return {}


def main() -> None:
    ap = argparse.ArgumentParser(prog="paperwatch")
    ap.add_argument("--config", type=pathlib.Path, default=None)
    ap.add_argument("--data-dir", type=pathlib.Path, default=pathlib.Path("data"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_in = sub.add_parser("ingest", help="共享湖增量采集(每日)")
    p_in.add_argument("--field", required=True, help="lake.fields 中的学科名")
    p_in.add_argument("--since", default=None, help="YYYY-MM-DD(首轮必填;后续用游标推进)")
    sub.add_parser("sync-retractions", help="RW 撤稿库同步(每日)")
    p_rep = sub.add_parser("report", help="生成周报(每周)")
    p_rep.add_argument("--profile", type=pathlib.Path, required=True,
                       help="档案 JSON:{positives:[paper_id], negatives:[paper_id]}")
    p_rep.add_argument("--venues", type=pathlib.Path, default=None,
                       help="venue 特征查表 JSON(装载器产物;缺省时分级降级为数据不足)")
    p_rep.add_argument("--allow-stale-retractions", action="store_true",
                       help="显式允许在撤稿库缺失时出报告(默认 fail-loud,kb 15.1)")
    args = ap.parse_args()

    cfg = config.load(args.config)
    args.data_dir.mkdir(parents=True, exist_ok=True)
    store = args.data_dir / "papers.jsonl"   # ⚠ 临时形态:定稿为 kb 14 章 SQLite(BACKLOG #1)

    if args.cmd == "ingest":
        lake = OpenAlexLake(cfg["lake"], args.data_dir / "lake_state.json")
        papers = lake.fetch_field(cfg["lake"]["fields"][args.field], args.since)
        with open(store, "a", encoding="utf-8") as f:
            for p in papers:
                f.write(json.dumps(p.__dict__, ensure_ascii=False) + "\n")
        st = lake.state.get(str(cfg["lake"]["fields"][args.field]), {})
        print(f"ingested {len(papers)} works; budget used {lake.state['budget']['used']}"
              + (";⚠ incomplete — 游标已保存,下轮续拉" if st.get("incomplete") else ""))

    elif args.cmd == "sync-retractions":
        idx = RetractionIndex(args.data_dir / "retractions.csv")
        n = idx.sync(cfg["lake"]["mailto"])
        print(f"synced: {n} retractions (+{len(idx._concerns)} expressions of concern)")

    elif args.cmd == "report":
        idx = RetractionIndex(args.data_dir / "retractions.csv")
        retraction_status = "未同步"
        if (args.data_dir / "retractions.csv").exists():
            idx.load()
            retraction_status = f"已加载(撤稿 {len(idx._retracted)} 条)"
        elif not args.allow_stale_retractions:
            sys.exit("撤稿库缺失:先运行 sync-retractions,或显式加 --allow-stale-retractions"
                     "(kb 15.1:撤稿比对为每日必做,不允许静默跳过)")
        raw = [Paper(**json.loads(l)) for l in store.read_text(encoding="utf-8").splitlines()]
        pool = dedup(raw, cfg["dedup"])
        vfeats = _load_venue_features(args.venues)
        prof = json.loads(args.profile.read_text())
        ranker = ProfileRanker(cfg["ranking"])
        by_id = {p.paper_id: p for p in pool}
        for pid in prof.get("positives", []):
            if pid in by_id:
                ranker.feedback(by_id[pid], useful=True)
        for pid in prof.get("negatives", []):
            if pid in by_id:
                ranker.feedback(by_id[pid], useful=False)
        scores, confs = ranker.score(pool, pool)
        scored = []
        for p, s, c in zip(pool, scores, confs):
            vd = classify(vfeats[p.venue], cfg["venue_tiers"]) if p.venue in vfeats else None
            scored.append(assemble(p, s, c, vd, cfg["credibility"]))
        passed, blocked = run_gates(scored, idx)
        stat = {"sources": ["openalex"], "total": len(raw), "deduped": len(pool),
                "blocked": len(blocked), "retraction_status": retraction_status}
        print(build(passed, cfg["report"], stat))


if __name__ == "__main__":
    main()
