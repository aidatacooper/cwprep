# Copyright (C) 2025 Cooper Wenhua <imgwho@gmail.com>
# SPDX-License-Identifier: AGPL-3.0
"""Generate TFL/TFLX files from declarative specs."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

from .spec_io import flow_parts_from_spec, read_spec


def _resolve_output(args, spec):
    output = args.out or spec.get("output_path") or spec.get("output")
    if not output:
        raise ValueError("Output path is required. Use `--out` or set `output_path` in the spec.")
    return output


def _ensure_output_is_safe(path: str, force: bool):
    output_path = Path(path)
    if output_path.exists() and not force:
        raise FileExistsError(f"Output already exists: {path}. Use --force to overwrite.")


def run(args) -> int:
    from cwprep.mcp_server import generate_tfl, validate_flow_definition

    spec = read_spec(args.spec)
    flow_name, connection, nodes, data_files = flow_parts_from_spec(spec)
    output_path = _resolve_output(args, spec)
    validation = json.loads(validate_flow_definition(flow_name, connection, nodes))

    if args.dry_run:
        payload = {
            "valid": validation["valid"],
            "output_path": output_path,
            "flow_name": flow_name,
            "node_count": len(nodes),
            "errors": validation["errors"],
        }
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        elif validation["valid"]:
            print(f"Dry run OK: {flow_name} -> {output_path} ({len(nodes)} nodes)")
        else:
            print("Dry run failed:")
            for error in validation["errors"]:
                print(f"  - {error}")
        return 0 if validation["valid"] else 1

    if not validation["valid"]:
        if args.json:
            print(json.dumps(validation, indent=2, ensure_ascii=False))
        else:
            print("Invalid flow spec:")
            for error in validation["errors"]:
                print(f"  - {error}")
        return 1

    _ensure_output_is_safe(output_path, args.force)

    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        summary = generate_tfl(flow_name, connection, nodes, output_path, data_files=data_files)

    payload = {
        "ok": True,
        "output_path": str(Path(output_path).resolve()),
        "flow_name": flow_name,
        "node_count": len(nodes),
        "summary": summary,
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(summary)
    return 0
