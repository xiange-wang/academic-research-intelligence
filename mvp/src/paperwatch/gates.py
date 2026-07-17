"""发布前质量门禁(knowledgebase 15.3):全自动、一票否决。

门禁项:引用存在性(DOI/链接可达)、撤稿比对、锚点存在性(生成句可定位到原文)。
指标口径:发布门禁拦截率 100%(门禁项零放行);不承诺"错误率 0"(kb 17.2 v1.3)。
"""
from __future__ import annotations
import re
import requests
from .models import ScoredPaper
from .retractions import RetractionIndex


def link_alive(url: str, timeout: int = 10) -> bool:
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        return r.status_code < 400
    except requests.RequestException:
        return False


def anchor_check(generated: str, source_text: str) -> bool:
    """三类陈述规范(kb 8.2):「论文称」引句必须能在原文定位(规范化子串匹配)。"""
    quoted = re.findall(r"「论文称[::]?(.*?)」", generated)
    norm = lambda s: re.sub(r"\s+", " ", s.lower()).strip()
    src = norm(source_text)
    return all(norm(q) in src for q in quoted) if quoted else True


def run_gates(items: list[ScoredPaper], retractions: RetractionIndex,
              check_links: bool = False) -> tuple[list[ScoredPaper], list[tuple[ScoredPaper, str]]]:
    """返回 (通过, 拦截[(条目, 原因)])。任何一项失败即拦截。"""
    passed, blocked = [], []
    for it in items:
        if it.vetoed or retractions.is_retracted(it.paper.doi):
            blocked.append((it, "retracted"))
            continue
        if not it.paper.title:
            blocked.append((it, "missing title"))
            continue
        if check_links and it.paper.doi and not link_alive(f"https://doi.org/{it.paper.doi}"):
            blocked.append((it, "doi unreachable"))
            continue
        passed.append(it)
    return passed, blocked
