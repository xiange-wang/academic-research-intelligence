"""去重与版本合并(knowledgebase 15.4)。

原则:错误合并代价高于漏合并 -> 精确 ID 匹配优先,模糊匹配保守阈值 + 作者重叠要求。
预印本↔正式版合并为一条记录并保留版本历史;报告引用正式版、标注预印本首发时间。
"""
from __future__ import annotations
import re
from difflib import SequenceMatcher
from .models import Paper


def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9一-鿿]+", " ", t.lower()).strip()


def _author_overlap(a: list[str], b: list[str]) -> bool:
    la = {x.split()[-1].lower() for x in a if x}
    lb = {x.split()[-1].lower() for x in b if x}
    return bool(la & lb) if la and lb else False


def merge(primary: Paper, dup: Paper) -> Paper:
    """合并副本:正式版字段优先;版本历史保留(kb 15.4/8.1A 双时间戳)。"""
    if dup.doc_type != "preprint" and primary.doc_type == "preprint":
        primary, dup = dup, primary
    primary.versions.extend([*dup.versions, dup.paper_id])
    primary.preprint_date = primary.preprint_date or (
        dup.pub_date if dup.doc_type == "preprint" else dup.preprint_date)
    primary.doi = primary.doi or dup.doi
    primary.arxiv_id = primary.arxiv_id or dup.arxiv_id
    primary.openalex_id = primary.openalex_id or dup.openalex_id
    primary.abstract = primary.abstract or dup.abstract
    return primary


def dedup(papers: list[Paper], cfg: dict) -> list[Paper]:
    out: list[Paper] = []
    by_key: dict[str, Paper] = {}
    for p in papers:
        hit = next((by_key[k] for k in p.key_candidates() if k in by_key), None)
        if hit is None:
            nt = _norm_title(p.title)
            for q in out:  # 保守模糊匹配
                if SequenceMatcher(None, nt, _norm_title(q.title)).ratio() >= cfg["title_similarity_threshold"] \
                        and (not cfg["require_author_overlap"] or _author_overlap(p.authors, q.authors)):
                    hit = q
                    break
        if hit is None:
            out.append(p)
        else:
            merged = merge(hit, p)
            if merged is not hit:  # 主记录发生交换(正式版取代预印本)
                out[out.index(hit)] = merged
        for k in (p.key_candidates() + ((hit or p).key_candidates() if hit else [])):
            by_key[k] = hit if hit is not None else p
    return out
