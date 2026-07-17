"""个性化排序:Scholar Inbox 配方(knowledgebase 11.2,v1.2 裁决)。

- 冻结嵌入只做表示;排序交给每档案一个逻辑回归。
- 负样本 = 显式"无关"(归因式) + 随机采样未交互论文作 easy negatives。
- 冷启动 5 正 + 3 负;每次反馈即重训(秒级,LR 足够小)。
- 分数线性缩放到 [-100, 100]。
- 无摘要论文走降级路径:仅标题嵌入 + 置信度下调(实验2:约 25-30% 无摘要)。
"""
from __future__ import annotations
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from .models import Paper


class Embedder:
    """可替换实现:生产用 GTE 类 sentence-transformers(kb 7.3 选型,待实验 7 裁决);
    骨架用 HashingVectorizer 保证零依赖可测。接口不变,换实现不改调用方。"""

    def __init__(self, dim: int = 256, no_abstract_penalty: float = 0.3):
        self._vec = HashingVectorizer(n_features=dim, alternate_sign=False, norm="l2")
        self._no_abs_conf = 1.0 - no_abstract_penalty   # 配置驱动(评审 L2)

    def embed(self, papers: list[Paper]) -> tuple[np.ndarray, np.ndarray]:
        """返回 (矩阵, 置信度向量)。无摘要 -> 仅标题 + 置信度降级。"""
        texts, conf = [], []
        for p in papers:
            if p.abstract:
                texts.append(f"{p.title} [SEP] {p.abstract}")
                conf.append(1.0)
            else:
                texts.append(p.title)
                conf.append(self._no_abs_conf)
        return self._vec.transform(texts).toarray(), np.array(conf)


class ProfileRanker:
    """一个主题档案一个 LR。归因门控:只有明确归因的负反馈进入训练(kb 10.4)。"""

    def __init__(self, cfg: dict, embedder: Embedder | None = None):
        self.cfg = cfg
        self.embedder = embedder or Embedder(
            no_abstract_penalty=cfg.get("no_abstract_confidence_penalty", 0.3))
        self.pos: list[Paper] = []
        self.neg: list[Paper] = []
        self._clf: LogisticRegression | None = None

    def feedback(self, paper: Paper, useful: bool, attributed: bool = True) -> None:
        if not useful and not attributed:
            return  # "其他"原因不更新模型(Feedly 模式)
        (self.pos if useful else self.neg).append(paper)
        self._clf = None  # 触发重训

    def _train(self, pool: list[Paper]) -> None:
        if len(self.pos) < self.cfg["cold_start_min_pos"] or len(self.neg) < self.cfg["cold_start_min_neg"]:
            raise ValueError(
                f"cold start needs >= {self.cfg['cold_start_min_pos']} pos / "
                f"{self.cfg['cold_start_min_neg']} neg (kb 11.2)")
        seen = {p.paper_id for p in self.pos + self.neg}
        rng = np.random.default_rng(42)
        candidates = [p for p in pool if p.paper_id not in seen]
        k = min(self.cfg["easy_negatives"], len(candidates))
        easy = list(rng.choice(np.array(candidates, dtype=object), size=k, replace=False)) if k else []
        papers = self.pos + self.neg + easy
        y = np.array([1] * len(self.pos) + [0] * (len(self.neg) + len(easy)))
        X, _ = self.embedder.embed(papers)
        # 加权:正负样本平衡(Scholar Inbox 加权 BCE 的 sklearn 等价近似)
        clf = LogisticRegression(C=self.cfg["lr_C"], class_weight="balanced", max_iter=1000)
        clf.fit(X, y)
        self._clf = clf

    def score(self, papers: list[Paper], pool: list[Paper]) -> tuple[np.ndarray, np.ndarray]:
        """返回 (分数[-100,100], 置信度)。分数即 kb 6.5 的相关性维实现。"""
        if self._clf is None:
            self._train(pool)
        X, conf = self.embedder.embed(papers)
        proba = self._clf.predict_proba(X)[:, 1]
        lo, hi = self.cfg["score_range"]
        return lo + proba * (hi - lo), conf
