# Copyright (C) 2025 Cooper Wenhua <imgwho@gmail.com>
# SPDX-License-Identifier: AGPL-3.0
"""Human-friendly CLI and smart MCP entrypoint for cwprep."""

from __future__ import annotations

import argparse
import os
import sys

from cwprep import __version__


DESCRIPTION = "cwprep - Tableau Prep flow engineering toolkit and MCP server"


def _add_json(parser):
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cwprep",
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Smart entry:\n"
            "  With no arguments, cwprep starts MCP only when stdin is not a TTY.\n"
            "  In an interactive terminal, it prints this help.\n"
        ),
    )
    parser.add_argument("--version", action="version", version=f"cwprep {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    mcp = subparsers.add_parser("mcp", help="Start MCP server over stdio or streamable HTTP.")
    mcp.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    mcp.add_argument("--host", default="0.0.0.0")
    mcp.add_argument("--port", type=int, default=8000)
    mcp.set_defaults(handler=_handle_mcp)

    doctor = subparsers.add_parser("doctor", help="Check installation and runtime dependencies.")
    _add_json(doctor)
    doctor.set_defaults(handler=_handle_doctor)

    status = subparsers.add_parser("status", help="Show version, paths, and runtime status.")
    _add_json(status)
    status.set_defaults(handler=_handle_status)

    capabilities = subparsers.add_parser("capabilities", help="List supported flow operations.")
    _add_json(capabilities)
    capabilities.set_defaults(handler=_handle_capabilities)

    validate = subparsers.add_parser("validate", help="Validate a JSON/YAML flow spec.")
    validate.add_argument("spec")
    _add_json(validate)
    validate.set_defaults(handler=_handle_validate)

    run = subparsers.add_parser("run", help="Generate a .tfl/.tflx file from a JSON/YAML spec.")
    run.add_argument("spec")
    run.add_argument("--out", help="Output .tfl/.tflx path. Overrides spec output_path.")
    run.add_argument("--dry-run", action="store_true", help="Validate and summarize without writing.")
    run.add_argument("--force", action="store_true", help="Allow replacing an existing output path.")
    _add_json(run)
    run.set_defaults(handler=_handle_run)

    translate = subparsers.add_parser("translate", help="Translate a JSON/YAML flow spec to SQL.")
    translate.add_argument("spec")
    translate.add_argument("--out", help="Optional SQL output path.")
    translate.set_defaults(handler=_handle_translate_spec)

    translate_tfl = subparsers.add_parser("translate-tfl", help="Translate an existing .tfl file to SQL.")
    translate_tfl.add_argument("tfl_path")
    translate_tfl.add_argument("--out", help="Optional SQL output path.")
    translate_tfl.set_defaults(handler=_handle_translate_tfl)

    return parser


def _handle_mcp(args) -> int:
    from cwprep.mcp_server import run_mcp_server

    run_mcp_server(transport=args.transport, host=args.host, port=args.port)
    return 0


def _handle_doctor(args) -> int:
    from cwprep.commands import doctor

    return doctor.run(args)


def _handle_status(args) -> int:
    from cwprep.commands import status

    return status.run(args)


def _handle_capabilities(args) -> int:
    from cwprep.commands import capabilities

    return capabilities.run(args)


def _handle_validate(args) -> int:
    from cwprep.commands import validate

    return validate.run(args)


def _handle_run(args) -> int:
    from cwprep.commands import run

    return run.run(args)


def _handle_translate_spec(args) -> int:
    from cwprep.commands import translate

    return translate.run_spec(args)


def _handle_translate_tfl(args) -> int:
    from cwprep.commands import translate

    return translate.run_tfl(args)


def _run_mcp_from_env_or_stdin(argv, parser) -> int:
    mode = os.environ.get("CWPREP_MODE", "").strip().lower()
    if mode == "mcp":
        return _handle_mcp(argparse.Namespace(transport="stdio", host="0.0.0.0", port=8000))
    if mode == "cli":
        parser.print_help()
        return 0
    if not argv:
        if sys.stdin.isatty():
            parser.print_help()
            return 0
        return _handle_mcp(argparse.Namespace(transport="stdio", host="0.0.0.0", port=8000))
    return None


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    parser = build_parser()
    smart_result = _run_mcp_from_env_or_stdin(argv, parser)
    if smart_result is not None:
        return smart_result

    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 0

    try:
        return args.handler(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
