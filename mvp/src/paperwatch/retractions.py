"""撤稿同步(knowledgebase 15.1)。

主源:Crossref/Retraction Watch 合并 CSV(每工作日更新,免费开放)。
不要只靠 Crossmark(会漏约 2/3)。交叉:OpenAlex is_retracted(采集时已带)。

语义(评审 H2 修复):按 RetractionNature 区分——只有 Retraction 进一票否决索引;
Expression of concern 单独建索引(供扣分制/人工复核);Reinstatement 从否决索引移除;
Correction 不否决。命中 -> 库内红旗;已进过报告 -> 追溯更正通知(报告不可变,通知另发)。
"""
from __future__ import annotations
import csv, io, pathlib
import requests

RW_CSV_URL = "https://api.labs.crossref.org/data/retractionwatch"


def _norm_doi(doi: str) -> str:
    return doi.strip().lower().removeprefix("https://doi.org/")


class RetractionIndex:
    def __init__(self, cache: pathlib.Path):
        self.cache = cache
        self._retracted: set[str] = set()
        self._concerns: set[str] = set()
        self.loaded = False

    def sync(self, email: str, timeout: int = 120) -> int:
        """每日调用。下载 CSV 并重建索引;失败时沿用本地缓存(降级,kb 15.1)。"""
        try:
            r = requests.get(RW_CSV_URL, params={"mailto": email}, timeout=timeout)
            r.raise_for_status()
            self.cache.write_bytes(r.content)
        except requests.RequestException:
            if not self.cache.exists():
                raise
        self.load()
        return len(self._retracted)

    def load(self) -> None:
        """解析缓存 CSV。列名缺失即报错(评审 L4:防 HTML 错误页静默产出空索引)。"""
        rd = csv.DictReader(io.StringIO(self.cache.read_text(errors="replace")))
        cols = rd.fieldnames or []
        doi_col = next((c for c in cols if "doi" in c.lower() and "original" in c.lower()), None)
        nature_col = next((c for c in cols if "nature" in c.lower()), None)
        if not doi_col or not nature_col:
            raise ValueError(f"unexpected RW CSV columns: {cols[:8]} (need OriginalPaperDOI + RetractionNature)")
        reinstated: set[str] = set()
        for row in rd:
            doi = _norm_doi(row.get(doi_col) or "")
            if not doi or doi == "unavailable":
                continue
            nature = (row.get(nature_col) or "").strip().lower()
            if nature == "retraction":
                self._retracted.add(doi)
            elif "concern" in nature:
                self._concerns.add(doi)
            elif nature == "reinstatement":
                reinstated.add(doi)
            # correction:不否决(kb 6.5 语义)
        self._retracted -= reinstated
        self.loaded = True

    def is_retracted(self, doi: str | None) -> bool:
        return bool(doi) and _norm_doi(doi) in self._retracted

    def has_concern(self, doi: str | None) -> bool:
        return bool(doi) and _norm_doi(doi) in self._concerns
