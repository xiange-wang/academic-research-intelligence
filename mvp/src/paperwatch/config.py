"""配置加载:设计初值全部来自 YAML(knowledgebase 反复要求可配置、不硬编码)。"""
from __future__ import annotations
import pathlib
import yaml

DEFAULT = pathlib.Path(__file__).resolve().parents[2] / "config" / "default.yaml"


def load(path: pathlib.Path | None = None) -> dict:
    with open(path or DEFAULT, encoding="utf-8") as f:
        return yaml.safe_load(f)
