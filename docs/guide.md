# cwprep Guide

This page collects the detailed documentation that does not belong in the README.

## Python API

### As Python Library

Use `TFLBuilder(...)` to define a Tableau Prep flow graph, then use `TFLPackager` to write the final `.tfl` or `.tflx` archive.

```python
from cwprep import TFLBuilder, TFLPackager

builder = TFLBuilder(flow_name="Customer Orders")

conn_id = builder.add_connection(
    host="localhost",
    username="root",
    dbname="mydb",
)

orders = builder.add_input_table("Orders", "orders", conn_id)
customers = builder.add_input_table("Customers", "customers", conn_id)

joined = builder.add_join(
    name="Orders + Customers",
    left_id=orders,
    right_id=customers,
    left_col="customer_id",
    right_col="customer_id",
    join_type="left",
)

completed = builder.add_filter("Completed Orders", joined, "[status] = 'completed'")
builder.add_output_server("Output", completed, "Customer_Orders")

flow, display, meta = builder.build()
TFLPackager.save_tfl("./customer_orders.tfl", flow, display, meta)
```

### Working with Packaged Flows (.tflx)

`.tflx` files bundle the flow together with local data files. Use packaged flows when you want the generated artifact to be portable across machines.

```python
from cwprep import TFLBuilder, TFLPackager

builder = TFLBuilder(flow_name="Packaged Orders")
conn = builder.add_file_connection("orders.xlsx", is_packaged=True)
orders = builder.add_input_excel("Orders", "Sheet1", conn)
builder.add_output_server("Output", orders, "Packaged_Orders")

flow, display, meta = builder.build(is_packaged=True)
TFLPackager.save_tflx(
    "./packaged_orders.tflx",
    flow,
    display,
    meta,
    data_files={conn: ["C:/data/orders.xlsx"]},
)
```

By default, both the SDK and MCP output only the final `.tfl` or `.tflx` archive. Use `save_to_folder()` only when you explicitly want the exploded folder for inspection.

### SQL Translation

Use `SQLTranslator` when you want to inspect generated flow logic as ANSI SQL-style CTEs.

```python
from cwprep import SQLTranslator

translator = SQLTranslator()
sql = translator.translate_tfl_file("./customer_orders.tfl")
print(sql)
```

SQL translation is intended for review, documentation, and migration planning. Unsupported Tableau Prep functions are marked for human review instead of being silently rewritten.

## Connection Reference

### Database Connections

```python
# MySQL
conn = builder.add_connection("localhost", "root", "my_db")

# PostgreSQL
conn = builder.add_connection(
    host="localhost",
    username="postgres",
    dbname="my_db",
    db_class="postgres",
)

# SQL Server with Windows Authentication
conn = builder.add_connection(
    host="localhost",
    db_class="sqlserver",
    authentication="sspi",
)
orders = builder.add_input_table("Orders", "orders", conn, schema="dbo")
```

Supported `db_class` values:

| Value | Description |
|---|---|
| `mysql` | MySQL connection profile |
| `postgres` | PostgreSQL connection profile |
| `sqlserver` | SQL Server connection profile |
| `adb_mysql` | Alibaba AnalyticDB for MySQL connection profile |

### File Connections

```python
# Excel
conn = builder.add_file_connection("C:/data/orders.xlsx")
orders = builder.add_input_excel("Orders", "Sheet1", conn)

# CSV
conn = builder.add_file_connection("C:/data/orders.csv")
orders = builder.add_input_csv("Orders", conn)

# CSV union
conn = builder.add_file_connection("C:/data/orders", file_class="textscan")
orders = builder.add_input_csv_union(
    "Orders Union",
    conn,
    file_names=["orders_jan.csv", "orders_feb.csv"],
)
```

## Transform Reference

| Method | Description |
|---|---|
| `add_join` | Join two parent nodes; supports left, right, inner, full, and multi-column joins |
| `add_union` | Union multiple parent nodes |
| `add_filter` | Add an expression-based Tableau Prep filter |
| `add_value_filter` | Keep or exclude exact values without writing OR chains |
| `add_keep_only` | Keep selected columns |
| `add_remove_columns` | Drop selected columns |
| `add_rename` | Rename fields |
| `add_calculation` | Add a Tableau Prep calculated field |
| `add_quick_calc` | Apply quick clean operations such as uppercase, lowercase, trim, and remove spaces |
| `add_change_type` | Change field data types |
| `add_duplicate_column` | Duplicate a field |
| `add_aggregate` | Group by dimensions and aggregate measures |
| `add_pivot` | Pivot rows to columns |
| `add_unpivot` | Unpivot columns to rows |
| `add_output_server` | Add a Tableau Server output node |

### Calculation Syntax Notes

Tableau Prep calculation syntax is not SQL syntax. Common differences:

| SQL habit | Tableau Prep form |
|---|---|
| `[f] IN ('A','B')` | `[f] = 'A' OR [f] = 'B'` |
| `[f] != 'x'` | `[f] <> 'x'` |
| `[f] BETWEEN 1 AND 5` | `[f] >= 1 AND [f] <= 5` |
| `[f] = "text"` | `[f] = 'text'` |
| `[f] = NULL` | `ISNULL([f])` |

When using MCP, read `cwprep://docs/calculation-syntax` before creating formulas.

## MCP Reference

### MCP Tools

| Tool | Description |
|---|---|
| `generate_tfl` | Generate a `.tfl` or `.tflx` file from a declarative flow definition |
| `translate_to_sql` | Translate a flow definition or `.tfl` file to ANSI SQL |
| `list_supported_operations` | List supported node types and operation names |
| `validate_flow_definition` | Validate a flow definition before generating |

Recommended agent workflow:

```text
read resources -> design -> validate_flow_definition -> generate_tfl
```

### MCP Resources

| Resource | Description |
|---|---|
| `cwprep://docs/api-reference` | SDK and MCP API reference |
| `cwprep://docs/calculation-syntax` | Tableau Prep calculation syntax |
| `cwprep://docs/best-practices` | Common pitfalls and flow design rules |

### MCP Prompts

| Prompt | Description |
|---|---|
| `design_data_flow` | Interactive flow design assistant |
| `explain_tfl_structure` | TFL file structure explanation |

### Client Configuration

All clients below use the short `uvx cwprep` form. Equivalent explicit forms such as `uvx --from cwprep cwprep-mcp`, `cwprep-mcp`, and `python -m cwprep.mcp_server` remain supported.

#### Claude Desktop

Edit config file:

- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "cwprep": {
      "command": "uvx",
      "args": ["cwprep"]
    }
  }
}
```

#### Cursor

Settings -> MCP -> Add new MCP server, or edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "cwprep": {
      "command": "uvx",
      "args": ["cwprep"]
    }
  }
}
```

#### VSCode

Create `.vscode/mcp.json` in the project root:

```json
{
  "servers": {
    "cwprep": {
      "command": "uvx",
      "args": ["cwprep"]
    }
  }
}
```

#### Claude Code

```bash
claude mcp add cwprep -- uvx cwprep
```

#### Gemini CLI

Edit `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "cwprep": {
      "command": "uvx",
      "args": ["cwprep"]
    }
  }
}
```

#### Continue

Edit `~/.continue/config.yaml`:

```yaml
mcpServers:
  - name: cwprep
    command: uvx
    args:
      - cwprep
```

#### Remote HTTP Mode

Start the server:

```bash
cwprep-mcp --transport streamable-http --port 8000
```

Then configure your client with the endpoint:

```text
http://your-server-ip:8000/mcp
```

## Configuration

Create `config.yaml` for default settings:

```yaml
database:
  host: localhost
  port: 3306
  dbname: mydb
  type: mysql

tableau_server:
  url: http://your-server
  default_project: Default
```

SQL Server and PostgreSQL are also supported:

```yaml
# SQL Server with Windows Authentication
database:
  host: localhost
  type: sqlserver
  authentication: sspi
  schema: dbo

# PostgreSQL
database:
  host: localhost
  port: 5432
  dbname: mydb
  type: postgres
```

## Examples

The `examples/` directory contains complete demos based on the Sample Superstore dataset.

| Script | What it demonstrates |
|---|---|
| `examples/quick_start.py` | Minimal connect, join, filter, calculate, output workflow |
| `examples/demo_basic.py` | Input, join, and output |
| `examples/demo_cleaning.py` | Filter, value filter, keep only, rename, calculation, remove columns |
| `examples/demo_field_operations.py` | Quick clean, type change, and duplicate column |
| `examples/demo_aggregation.py` | Union, aggregate, pivot, and unpivot |
| `examples/demo_comprehensive.py` | End-to-end sales analysis flow |
| `examples/demo_mcp_flow.py` | MCP-friendly review demo with generated sample data |
| `examples/prompts.md` | Ready-to-use prompt templates for AI-driven flow generation |

Run an example:

```bash
python examples/quick_start.py
```

Open the generated `.tfl` or `.tflx` file in Tableau Prep Builder to inspect the result.

## Development

### Project Structure

```text
cwprep/
|-- .agents/skills/      # AI agent skill index
|-- src/cwprep/
|   |-- builder.py       # TFLBuilder
|   |-- packager.py      # TFLPackager
|   |-- translator.py    # SQLTranslator
|   |-- expression_translator.py
|   |-- config.py
|   |-- mcp_server.py
|   `-- references/      # MCP resource documents
|-- examples/
|-- docs/
|-- tests/
|-- pyproject.toml
`-- README.md
```

### Local Development

```bash
# Install in editable mode
pip install -e ".[dev]"

# Run tests
pytest

# Run the quick example
python examples/quick_start.py

# Start MCP server
cwprep
```
