"""arXiv 增量采集(knowledgebase 3.1.4)。

- 限速:1 请求 / 3 秒,单连接(官方 ToU)。
- 按 submittedDate 范围 + 分类检索;单次 <=2000 条。
- 元数据 CC0;全文不转储再分发(链接回 arxiv.org)。
"""
from __future__ import annotations
import time
import xml.etree.ElementTree as ET
import requests
from .models import Paper

API = "http://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}


def fetch(categories: list[str], date_from: str, date_to: str, cfg: dict,
          max_results: int = 1000) -> list[Paper]:
    """date_*: YYYYMMDDHHMM(arXiv submittedDate 语法)。"""
    cat_q = " OR ".join(f"cat:{c}" for c in categories)
    query = f"({cat_q}) AND submittedDate:[{date_from} TO {date_to}]"
    papers, start, page = [], 0, cfg["page_size"]
    while start < max_results:
        r = requests.get(API, params={
            "search_query": query, "start": start, "max_results": page,
            "sortBy": "submittedDate", "sortOrder": "ascending"}, timeout=60)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        entries = root.findall("a:entry", NS)
        if not entries:
            break
        for e in entries:
            aid = (e.findtext("a:id", "", NS) or "").rsplit("/abs/", 1)[-1]
            papers.append(Paper(
                paper_id=aid.split("v")[0],
                title=" ".join((e.findtext("a:title", "", NS) or "").split()),
                abstract=" ".join((e.findtext("a:summary", "", NS) or "").split()) or None,
                arxiv_id=aid.split("v")[0],
                authors=[a.findtext("a:name", "", NS) or "" for a in e.findall("a:author", NS)],
                pub_date=(e.findtext("a:published", "", NS) or "")[:10],
                doc_type="preprint",
                source="arxiv",
            ))
        start += page
        time.sleep(cfg["rate_limit_seconds"])   # 官方 ToU 限速
    return papers
