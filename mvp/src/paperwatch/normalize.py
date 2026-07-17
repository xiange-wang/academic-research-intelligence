"""去重与版本合并(knowledgebase 15.4)。

原则:错误合并代价高于漏合并 -> 精确 ID 匹配优先,模糊匹配保守阈值 + 作者重叠要求。
预印本↔正式版合并为一条记录并保留版本历史;报告引用正式版、标注预印本首发时间。

实现说明(评审 H1 修复):by_key 存 out 列表索引而非对象引用,合并交换主记录后
所有键统一重注册到同一索引,杜绝链式合并时的陈旧引用。
"""
from __future__ import annotations
import re
from difflib import SequenceMatcher
from .models import Paper


def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9一-鿿]+", " ", t.lower()).strip()


def _author_overlap(a: list[str], b: list[str]) -> bool:
    # 姓氏取末 token 的近似对中文序/单名作者会失真——方向是保守(漏合并),可接受(kb 15.4)
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


def _block_key(nt: str) -> str:
    """模糊匹配分桶键:规范化标题前 3 个词。只在同桶内做昂贵比较(评审 M4)。
    代价:首词不同的同文异题版本会漏合并——保守方向,符合 kb 15.4 原则。"""
    return " ".join(nt.split()[:3])


def dedup(papers: list[Paper], cfg: dict) -> list[Paper]:
    out: list[Paper] = []
    norm_titles: list[str] = []          # 与 out 同步的规范化标题缓存
    by_key: dict[str, int] = {}          # 精确键 -> out 索引(评审 H1)
    blocks: dict[str, list[int]] = {}    # 分桶键 -> out 索引列表
    thr = cfg["title_similarity_threshold"]
    for p in papers:
        idx = next((by_key[k] for k in p.key_candidates() if k in by_key), None)
        nt = _norm_title(p.title)
        bk = _block_key(nt)
        if idx is None:
            for i in blocks.get(bk, []):  # 仅同桶内模糊匹配
                existing_nt = norm_titles[i]
                if abs(len(existing_nt) - len(nt)) > max(8, len(nt) // 5):
                    continue
                if SequenceMatcher(None, nt, existing_nt).ratio() >= thr \
                        and (not cfg["require_author_overlap"]
                             or _author_overlap(p.authors, out[i].authors)):
                    idx = i
                    break
        if idx is None:
            out.append(p)
            norm_titles.append(nt)
            idx = len(out) - 1
            blocks.setdefault(bk, []).append(idx)
        else:
            merged = merge(out[idx], p)
            out[idx] = merged            # 主记录可能被交换,统一以 merged 为准
            new_nt = _norm_title(merged.title)
            if _block_key(new_nt) != _block_key(norm_titles[idx]):
                blocks.setdefault(_block_key(new_nt), []).append(idx)
            norm_titles[idx] = new_nt
        for k in (*p.key_candidates(), *out[idx].key_candidates()):
            by_key[k] = idx
    return out
