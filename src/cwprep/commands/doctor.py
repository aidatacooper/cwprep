# Copyright (C) 2025 Cooper Wenhua <imgwho@gmail.com>
# SPDX-License-Identifier: AGPL-3.0
"""Installation diagnostics for cwprep."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

from cwprep import __version__


def _check_module(name: str):
    return {
        "name": name,
        "available": importlib.util.find_spec(name) is not None,
    }


def run(args) -> int:
    package_dir = Path(__file__).resolve().parents[1]
    references_dir = package_dir / "references"
    checks = [
        _check_module("mcp"),
        _check_module("yaml"),
        _check_module("build"),
        _check_module("twine"),
        {
            "name": "reference_docs",
            "available": all(
                (references_dir / filename).is_file()
                for filename in (
                    "api_reference.md",
                    "calculation_syntax.md",
                    "best_practices.md",
                )
            ),
        },
        {
            "name": "git",
            "available": shutil.which("git") is not None,
        },
    ]
    ok = all(check["available"] for check in checks if check["name"] != "yaml")
    payload = {
        "ok": ok,
        "version": __version__,
        "python": sys.version.split()[0],
        "checks": checks,
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if ok else 1

    print(f"cwprep {__version__}")
    print(f"Python {payload['python']}")
    for check in checks:
        marker = "OK" if check["available"] else "MISSING"
        optional = " (optional)" if check["name"] == "yaml" else ""
        print(f"{marker:7} {check['name']}{optional}")
    return 0 if ok else 1
