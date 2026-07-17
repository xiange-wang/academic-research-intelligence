"""CLI:ingest / rank / report(节奏见 knowledgebase 12.3:日采集、周报告)。"""
from __future__ import annotations
import argparse, json, pathlib
from . import config
from .models import Paper
from .ingest_openalex import OpenAlexLake
from .normalize import dedup
from .retractions import RetractionIndex
from .report_weekly import build
from .ranking import ProfileRanker
from .scoring import assemble
from .gates import run_gates


def main() -> None:
    ap = argparse.ArgumentParser(prog="paperwatch")
    ap.add_argument("--config", type=pathlib.Path, default=None)
    ap.add_argument("--data-dir", type=pathlib.Path, default=pathlib.Path("data"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_in = sub.add_parser("ingest", help="共享湖增量采集(每日)")
    p_in.add_argument("--field", required=True, help="lake.fields 中的学科名")
    p_in.add_argument("--since", required=True, help="YYYY-MM-DD")
    sub.add_parser("sync-retractions", help="RW 撤稿库同步(每日)")
    p_rep = sub.add_parser("report", help="生成周报(每周)")
    p_rep.add_argument("--profile", type=pathlib.Path, required=True,
                       help="档案 JSON:{positives:[paper_id], negatives:[paper_id]}")
    args = ap.parse_args()

    cfg = config.load(args.config)
    args.data_dir.mkdir(parents=True, exist_ok=True)
    store = args.data_dir / "papers.jsonl"

    if args.cmd == "ingest":
        lake = OpenAlexLake(cfg["lake"], args.data_dir / "lake_state.json")
        papers = lake.fetch_field(cfg["lake"]["fields"][args.field], args.since)
        with open(store, "a", encoding="utf-8") as f:
            for p in papers:
                f.write(json.dumps(p.__dict__, ensure_ascii=False) + "\n")
        print(f"ingested {len(papers)} works ({lake.requests_today} requests)")

    elif args.cmd == "sync-retractions":
        idx = RetractionIndex(args.data_dir / "retractions.csv")
        print(f"synced {idx.sync(cfg['lake']['mailto'])} retraction records")

    elif args.cmd == "report":
        raw = [Paper(**json.loads(l)) for l in store.read_text(encoding="utf-8").splitlines()]
        pool = dedup(raw, cfg["dedup"])
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
        scored = [assemble(p, s, c, None, cfg["credibility"])
                  for p, s, c in zip(pool, scores, confs)]
        idx = RetractionIndex(args.data_dir / "retractions.csv")
        if (args.data_dir / "retractions.csv").exists():
            idx._load()
        passed, blocked = run_gates(scored, idx)
        stat = {"sources": ["openalex"], "total": len(raw),
                "deduped": len(pool), "blocked": len(blocked)}
        print(build(passed, cfg["report"], stat))


if __name__ == "__main__":
    main()
