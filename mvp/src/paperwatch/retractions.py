"""撤稿同步(knowledgebase 15.1)。

主源:Crossref/Retraction Watch 合并 CSV(每工作日更新,免费开放)。
不要只靠 Crossmark(会漏约 2/3)。交叉:OpenAlex is_retracted(采集时已带)。
命中 -> 库内红旗;已进过报告 -> 追溯更正通知(报告为不可变快照,通知另发)。
"""
from __future__ import annotations
import csv, io, pathlib
import requests

RW_CSV_URL = "https://api.labs.crossref.org/data/retractionwatch"


class RetractionIndex:
    def __init__(self, cache: pathlib.Path):
        self.cache = cache
        self._dois: set[str] = set()

    def sync(self, email: str, timeout: int = 120) -> int:
        """每日调用。下载 CSV 并重建 DOI 索引;失败时沿用本地缓存(降级,kb 15.1)。"""
        try:
            r = requests.get(f"{RW_CSV_URL}?mailto={email}", timeout=timeout)
            r.raise_for_status()
            self.cache.write_bytes(r.content)
        except requests.RequestException:
            if not self.cache.exists():
                raise
        self._load()
        return len(self._dois)

    def _load(self) -> None:
        text = self.cache.read_text(errors="replace")
        rd = csv.DictReader(io.StringIO(text))
        col = next((c for c in (rd.fieldnames or []) if "doi" in c.lower() and "original" in c.lower()),
                   next((c for c in (rd.fieldnames or []) if "doi" in c.lower()), None))
        self._dois = {row[col].strip().lower().removeprefix("https://doi.org/")
                      for row in rd if col and row.get(col)} if col else set()

    def is_retracted(self, doi: str | None) -> bool:
        return bool(doi) and doi.strip().lower().removeprefix("https://doi.org/") in self._dois
