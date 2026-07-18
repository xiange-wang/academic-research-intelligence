"""共享摄入湖:OpenAlex 按学科增量采集(knowledgebase 2.3、3.1.1)。

- 按 field 拉一次增量,所有档案本地匹配;禁止 per-user 持续性查询。
- 增量键(2026-07-17 实测):**from_created_date 为 Premium 限定过滤器**(免费层返回
  "Plan upgrade required")。因此:有 api_key 时用 from_created_date(真收录增量);
  免费层用 from_publication_date + **回看窗口**(lookback_days,每日重扫近 N 天,
  由 dedup 吸收重复)缓解晚收录漏采;更早的回填靠季度 snapshot 兜底。
- 游标真持久化:预算/页数耗尽时保存 next_cursor,下轮续拉;走完才推进 since。
- 预算护栏跨进程:计数带日期存入 state(评审 M3);耗尽返回已收集结果不丢数据。
- 保留 referenced_works / topics / cited_by_count 等字段(kb 14.1 边表与图特征依赖)。
"""
from __future__ import annotations
import json, os, pathlib, time
from datetime import date
import requests
from .models import Paper

API = "https://api.openalex.org/works"
FIELDS = ("id,doi,title,publication_date,type,is_retracted,abstract_inverted_index,"
          "authorships,primary_location,primary_topic,referenced_works,cited_by_count,"
          "open_access,language")


def _reconstruct_abstract(inv: dict | None) -> str | None:
    """倒排索引重建摘要——仅限内部 TDM 处理,不对外展示原文(kb 16.1 硬规则)。"""
    if not inv:
        return None
    pos = [(i, w) for w, idxs in inv.items() for i in idxs]
    return " ".join(w for _, w in sorted(pos)) or None


def _to_paper(w: dict) -> Paper:
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    p = Paper(
        paper_id=(w.get("doi") or w.get("id") or "").removeprefix("https://doi.org/"),
        title=w.get("title") or "",
        abstract=_reconstruct_abstract(w.get("abstract_inverted_index")),
        doi=(w.get("doi") or "").removeprefix("https://doi.org/") or None,
        openalex_id=w.get("id"),
        authors=[a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])],
        institutions=[i.get("display_name", "") for a in w.get("authorships", [])
                      for i in a.get("institutions", [])],
        venue=src.get("display_name"),
        pub_date=w.get("publication_date"),
        doc_type="preprint" if loc.get("version") == "submittedVersion" else (w.get("type") or "article"),
        is_retracted=bool(w.get("is_retracted")),
        source="openalex",
    )
    # 附加字段(kb 14.1:citations 边表 / topic 关系 / 图特征;骨架先随对象携带,入库时拆表)
    p.extra = {
        "referenced_works": w.get("referenced_works") or [],
        "topic_id": (w.get("primary_topic") or {}).get("id"),
        "field_id": ((w.get("primary_topic") or {}).get("field") or {}).get("id"),
        "cited_by_count": w.get("cited_by_count"),
        "oa_status": (w.get("open_access") or {}).get("oa_status"),
        "language": w.get("language"),
    }
    return p


class OpenAlexLake:
    def __init__(self, cfg: dict, state_path: pathlib.Path):
        self.cfg, self.state_path = cfg, state_path
        self.state = json.loads(state_path.read_text()) if state_path.exists() else {}
        today = date.today().isoformat()
        b = self.state.get("budget", {})
        self.state["budget"] = b if b.get("date") == today else {"date": today, "used": 0}

    def _budget_left(self) -> int:
        return self.cfg["daily_request_budget"] - self.state["budget"]["used"]

    def _save(self) -> None:
        tmp = self.state_path.with_suffix(".tmp")   # 原子写(评审 L11)
        tmp.write_text(json.dumps(self.state))
        os.replace(tmp, self.state_path)

    def fetch_field(self, field_id: int, since: str | None = None,
                    api_key: str | None = None, max_pages: int = 50) -> list[Paper]:
        """增量拉取。since 为空时用 state 中已完成的推进点;中断续拉自动衔接。"""
        from datetime import timedelta
        st = self.state.get(str(field_id), {})
        since = since or st.get("since")
        if not since:
            raise ValueError("first run must provide --since (YYYY-MM-DD)")
        cursor = st.get("cursor") or "*"
        # 续拉时必须复用首轮的确切 filter(评审复审 #2):OpenAlex cursor 绑定 mint 时的
        # query,免费层 date_filter 依赖 today 会跨天漂移使游标失效。故 incomplete 时存下
        # active_filter 原样复用;走完或新轮才重算。
        if st.get("incomplete") and st.get("active_filter"):
            date_filter = st["active_filter"]
        elif api_key:                     # Premium:真收录增量
            date_filter = f"from_created_date:{since}"
        else:                             # 免费层:发表日 + 回看窗口(dedup 吸收重复)
            lookback = self.cfg.get("lookback_days", 14)
            eff = min(date.fromisoformat(since), date.today() - timedelta(days=lookback))
            date_filter = f"from_publication_date:{eff.isoformat()}"
        papers, exhausted = [], False
        for _ in range(max_pages):
            if self._budget_left() <= 0:
                exhausted = True
                break
            params = {"filter": f"primary_topic.field.id:fields/{field_id},{date_filter}",
                      "select": FIELDS, "per-page": 200, "cursor": cursor,
                      "mailto": self.cfg["mailto"]}
            if api_key:
                params["api_key"] = api_key
            r = requests.get(API, params=params, timeout=60)
            self.state["budget"]["used"] += 1
            r.raise_for_status()
            data = r.json()
            papers.extend(_to_paper(w) for w in data.get("results", []))
            cursor = data.get("meta", {}).get("next_cursor")
            if not cursor or not data.get("results"):
                cursor = None
                break
            time.sleep(0.2)
        if cursor:  # 预算/页数耗尽:保存真游标 + 当轮 filter 续拉,不推进 since,不丢已取数据
            self.state[str(field_id)] = {"cursor": cursor, "since": since,
                                         "active_filter": date_filter, "incomplete": True}
        else:       # 走完:推进 since 到今天,游标与 filter 复位
            self.state[str(field_id)] = {"cursor": None, "since": date.today().isoformat(),
                                         "active_filter": None, "incomplete": False}
        self._save()
        # exhausted 时已收集结果照常返回;调用方从 state[field]["incomplete"] 看到续拉需求
        return papers
