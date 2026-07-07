# Copyright (C) 2025 Cooper Wenhua <imgwho@gmail.com>
# SPDX-License-Identifier: AGPL-3.0
"""Helpers for reading declarative cwprep flow specifications."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def read_spec(path: str) -> Dict[str, Any]:
    """Read a JSON or YAML flow specification from disk."""
    spec_path = Path(path)
    if not spec_path.is_file():
        raise FileNotFoundError(f"Spec file not found: {path}")

    text = spec_path.read_text(encoding="utf-8")
    suffix = spec_path.suffix.lower()

    if suffix == ".json":
        data = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError(
                "YAML specs require PyYAML. Install with `pip install cwprep[yaml]`."
            ) from exc
        data = yaml.safe_load(text)
    else:
        raise ValueError("Spec file must use .json, .yaml, or .yml extension.")

    if not isinstance(data, dict):
        raise ValueError("Spec file must contain a top-level object.")
    return data


def flow_parts_from_spec(spec: Dict[str, Any]):
    """Return flow_name, connection, nodes, and data_files from a spec object."""
    flow_name = spec.get("flow_name") or spec.get("name") or "Untitled Flow"
    connection = spec.get("connection")
    nodes = spec.get("nodes")
    data_files = spec.get("data_files")

    if not isinstance(connection, dict):
        raise ValueError("Spec must include a `connection` object.")
    if not isinstance(nodes, list):
        raise ValueError("Spec must include a `nodes` list.")

    return flow_name, connection, nodes, data_files
