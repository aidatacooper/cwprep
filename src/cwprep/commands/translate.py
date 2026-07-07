# Copyright (C) 2025 Cooper Wenhua <imgwho@gmail.com>
# SPDX-License-Identifier: AGPL-3.0
"""Translate flow definitions or TFL files to SQL."""

from __future__ import annotations

from pathlib import Path

from .spec_io import flow_parts_from_spec, read_spec


def _write_or_print(sql: str, output: str = None):
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(sql, encoding="utf-8")
        print(f"Wrote SQL: {out_path.resolve()}")
    else:
        print(sql)


def run_spec(args) -> int:
    from cwprep.mcp_server import translate_to_sql

    spec = read_spec(args.spec)
    flow_name, connection, nodes, _data_files = flow_parts_from_spec(spec)
    sql = translate_to_sql(flow_name=flow_name, connection=connection, nodes=nodes)
    _write_or_print(sql, args.out)
    return 0


def run_tfl(args) -> int:
    from cwprep.mcp_server import translate_to_sql

    sql = translate_to_sql(tfl_path=args.tfl_path)
    _write_or_print(sql, args.out)
    return 0
