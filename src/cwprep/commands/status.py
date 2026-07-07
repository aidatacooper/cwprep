# Copyright (C) 2025 Cooper Wenhua <imgwho@gmail.com>
# SPDX-License-Identifier: AGPL-3.0
"""Status command for cwprep."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from cwprep import __version__


def run(args) -> int:
    package_dir = Path(__file__).resolve().parents[1]
    payload = {
        "version": __version__,
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "package_dir": str(package_dir),
        "cwd": os.getcwd(),
        "mcp_entrypoint": "cwprep-mcp",
        "smart_entrypoint": "cwprep",
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print(f"cwprep {payload['version']}")
    print(f"Python: {payload['python']}")
    print(f"Executable: {payload['executable']}")
    print(f"Package: {payload['package_dir']}")
    print(f"Working directory: {payload['cwd']}")
    print("MCP: use `cwprep mcp` or `cwprep-mcp`")
    return 0
