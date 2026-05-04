# Copyright (C) 2025 Cooper Wenhua <imgwho@gmail.com>
# SPDX-License-Identifier: AGPL-3.0
"""
cwprep - Tableau Prep Flow SDK

Programmatically generate Tableau Prep data flow files (.tfl).

Usage:
    from cwprep import TFLBuilder, TFLPackager
    
    builder = TFLBuilder(flow_name="My Flow")
    conn_id = builder.add_connection(host="localhost", username="root", dbname="mydb")
    input1 = builder.add_input_sql("Users", "SELECT * FROM users", conn_id)
    builder.add_output_server("Output", input1, "Datasource Name")
    
    flow, display, meta = builder.build()
    TFLPackager.save_tfl("./output.tfl", flow, display, meta)
"""

from .builder import TFLBuilder
from .packager import TFLPackager
from .translator import SQLTranslator
from .expression_translator import ExpressionTranslator
from .config import (
    TFLConfig, 
    DatabaseConfig, 
    TableauServerConfig, 
    load_config,
    DEFAULT_CONFIG
)

__version__ = "0.5.6"
__author__ = "Cooper Wenhua"
__email__ = "imgwho@gmail.com"
__copyright__ = "Copyright (C) 2025 Cooper Wenhua <imgwho@gmail.com>"
__license__ = "AGPL-3.0"
__all__ = [
    "TFLBuilder", 
    "TFLPackager", 
    "SQLTranslator",
    "ExpressionTranslator",
    "TFLConfig", 
    "DatabaseConfig", 
    "TableauServerConfig", 
    "load_config",
    "DEFAULT_CONFIG",
    "__version__"
]

# MCP Server is available via `cwprep.mcp_server` (install with `pip install cwprep`)
# Usage: cwprep-mcp  or  python -m cwprep.mcp_server
