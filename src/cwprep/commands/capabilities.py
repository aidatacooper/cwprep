# Copyright (C) 2025 Cooper Wenhua <imgwho@gmail.com>
# SPDX-License-Identifier: AGPL-3.0
"""Capability listing command."""

from __future__ import annotations

import json


def run(args) -> int:
    from cwprep.mcp_server import list_supported_operations

    operations = json.loads(list_supported_operations())
    if args.json:
        print(json.dumps({"operations": operations}, indent=2, ensure_ascii=False))
        return 0

    print("Supported operations:")
    for op in operations:
        required = ", ".join(op.get("required", [])) or "-"
        print(f"  {op['type']}: {op['description']}")
        print(f"    required: {required}")
    return 0
