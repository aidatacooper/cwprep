# Copyright (C) 2025 Cooper Wenhua <imgwho@gmail.com>
# SPDX-License-Identifier: AGPL-3.0
"""Validate declarative flow specs."""

from __future__ import annotations

import json

from .spec_io import flow_parts_from_spec, read_spec


def run(args) -> int:
    from cwprep.mcp_server import validate_flow_definition

    spec = read_spec(args.spec)
    flow_name, connection, nodes, _data_files = flow_parts_from_spec(spec)
    result = json.loads(validate_flow_definition(flow_name, connection, nodes))

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif result["valid"]:
        print(f"Valid flow spec: {args.spec}")
    else:
        print(f"Invalid flow spec: {args.spec}")
        for error in result["errors"]:
            print(f"  - {error}")

    return 0 if result["valid"] else 1
