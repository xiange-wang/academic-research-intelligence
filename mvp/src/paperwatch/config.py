"""配置加载:设计初值全部来自 YAML(knowledgebase 反复要求可配置、不硬编码)。"""
from __future__ import annotations
import pathlib
import yaml

DEFAULT = pathlib.Path(__file__).resolve().parents[2] / "config" / "default.yaml"


def load(path: pathlib.Path | None = None) -> dict:
    import os
    with open(path or DEFAULT, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if os.environ.get("PAPERWATCH_MAILTO"):      # 真实邮箱走环境变量,不进仓库
        cfg["lake"]["mailto"] = os.environ["PAPERWATCH_MAILTO"]
    return cfg
