"""核心数据模型。对应 knowledgebase 8.1 论文卡片四区与 14 章实体草案。"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Paper:
    paper_id: str                       # 主键:DOI 优先,否则 openalex_id / arxiv_id
    title: str
    abstract: str | None = None         # 约 25–30% 无摘要(实验2),None 触发降级路径
    doi: str | None = None
    arxiv_id: str | None = None
    openalex_id: str | None = None
    authors: list[str] = field(default_factory=list)
    institutions: list[str] = field(default_factory=list)
    venue: str | None = None
    pub_date: str | None = None         # ISO;预印本首发与正式发表分开存
    preprint_date: str | None = None
    doc_type: str = "article"           # article/review/preprint/guideline/dataset/comment
    is_retracted: bool = False
    source: str = "openalex"
    versions: list[str] = field(default_factory=list)   # 版本合并历史(kb 15.4)

    def key_candidates(self) -> list[str]:
        return [k for k in (self.doi, self.arxiv_id, self.openalex_id) if k]


@dataclass
class VenueDecision:
    """kb 5.2:每个判定输出 级别+触发规则ID+原始指标值+快照日期。"""
    tier: str                           # S/A/B/normal/warning
    rule_ids: list[str]
    red_flags: list[str]                # 命中的 R1–R7
    demoted: bool
    raw: dict
    snapshot_date: str


@dataclass
class ScoredPaper:
    paper: Paper
    relevance: float                    # LR 输出,[-100,100](kb 6.5 分工:排序用它)
    credibility: float                  # 扣分制结果
    venue: VenueDecision | None
    confidence: float = 1.0             # 特征缺失(如无摘要)时下调并在卡片标注
    vetoed: bool = False                # 撤稿一票否决
    notes: list[str] = field(default_factory=list)
