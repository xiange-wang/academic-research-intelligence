"""共享摄入湖:OpenAlex 按学科增量采集(knowledgebase 2.3、3.1.1)。

- 按 field 拉一次增量,所有档案本地匹配;禁止 per-user 持续性查询。
- 游标持久化(json 文件);请求预算护栏(无 key ~100 次/天)。
- 实测(2026-07-17):日增 1.8-4.9 万篇/天(全学科),单学科在预算内。
"""
from __future__ import annotations
import json, pathlib, time
import requests
from .models import Paper

API = "https://api.openalex.org/works"


def _reconstruct_abstract(inv: dict | None) -> str | None:
    """倒排索引重建摘要——仅限内部 TDM 处理,不对外展示原文(kb 16.1 硬规则)。"""
    if not inv:
        return None
    pos = [(i, w) for w, idxs in inv.items() for i in idxs]
    return " ".join(w for _, w in sorted(pos)) or None


def _to_paper(w: dict) -> Paper:
    return Paper(
        paper_id=(w.get("doi") or w.get("id") or "").removeprefix("https://doi.org/"),
        title=w.get("title") or "",
        abstract=_reconstruct_abstract(w.get("abstract_inverted_index")),
        doi=(w.get("doi") or "").removeprefix("https://doi.org/") or None,
        openalex_id=w.get("id"),
        authors=[a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])],
        institutions=[i.get("display_name", "") for a in w.get("authorships", [])
                      for i in a.get("institutions", [])],
        venue=(w.get("primary_location") or {}).get("source", {}).get("display_name")
        if (w.get("primary_location") or {}).get("source") else None,
        pub_date=w.get("publication_date"),
        doc_type="preprint" if (w.get("primary_location") or {}).get("version") == "submittedVersion"
        else (w.get("type") or "article"),
        is_retracted=bool(w.get("is_retracted")),
        source="openalex",
    )


class OpenAlexLake:
    def __init__(self, cfg: dict, state_path: pathlib.Path):
        self.cfg, self.state_path = cfg, state_path
        self.state = json.loads(state_path.read_text()) if state_path.exists() else {}
        self.requests_today = 0

    def _guard(self) -> None:
        if self.requests_today >= self.cfg["daily_request_budget"]:
            raise RuntimeError("daily request budget exhausted (kb 2.3 成本护栏)")

    def fetch_field(self, field_id: int, since: str, api_key: str | None = None,
                    max_pages: int = 50) -> list[Paper]:
        """按 field 增量拉取:publication_date >= since,游标分页。"""
        papers, cursor = [], self.state.get(str(field_id), {}).get("cursor", "*")
        for _ in range(max_pages):
            self._guard()
            params = {
                "filter": f"primary_topic.field.id:fields/{field_id},from_publication_date:{since}",
                "per-page": 200, "cursor": cursor, "mailto": self.cfg["mailto"],
            }
            if api_key:
                params["api_key"] = api_key
            r = requests.get(API, params=params, timeout=60)
            self.requests_today += 1
            r.raise_for_status()
            data = r.json()
            papers.extend(_to_paper(w) for w in data.get("results", []))
            cursor = data.get("meta", {}).get("next_cursor")
            if not cursor or not data.get("results"):
                break
            time.sleep(0.2)
        self.state[str(field_id)] = {"cursor": "*", "last_since": since}  # 幂等:下轮重置游标按日期推进
        self.state_path.write_text(json.dumps(self.state))
        return papers
