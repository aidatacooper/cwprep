# cwprep 指南

本页收集不适合放进 README 的详细文档。

## Python API

### 作为 Python Library 使用

使用 `TFLBuilder(...)` 定义 Tableau Prep flow graph，然后用 `TFLPackager` 写出最终 `.tfl` 或 `.tflx` archive。

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

### 处理打包 Flow（.tflx）

`.tflx` 会把 flow 和本地数据文件一起打包。需要让生成 artifact 在不同机器间可移植时使用 packaged flows。

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

默认情况下，SDK 和 MCP 都只输出最终 `.tfl` 或 `.tflx` archive。只有明确需要 exploded folder 检查时才使用 `save_to_folder()`。

### SQL Translation

当你想把生成的 flow logic 作为 ANSI SQL 风格 CTEs 审查时，使用 `SQLTranslator`。

```python
from cwprep import SQLTranslator

translator = SQLTranslator()
sql = translator.translate_tfl_file("./customer_orders.tfl")
print(sql)
```

SQL translation 主要用于 review、documentation 和 migration planning。Unsupported Tableau Prep functions 会标记给人工审查，而不是静默重写。

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

支持的 `db_class`：

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
| `add_join` | Join 两个 parent nodes；支持 left、right、inner、full 和 multi-column joins |
| `add_union` | Union 多个 parent nodes |
| `add_filter` | 添加基于表达式的 Tableau Prep filter |
| `add_value_filter` | 按精确值 keep 或 exclude，避免手写 OR chains |
| `add_keep_only` | 保留指定列 |
| `add_remove_columns` | 删除指定列 |
| `add_rename` | 重命名字段 |
| `add_calculation` | 添加 Tableau Prep calculated field |
| `add_quick_calc` | 应用 uppercase、lowercase、trim、remove spaces 等 quick clean |
| `add_change_type` | 修改字段数据类型 |
| `add_duplicate_column` | 复制字段 |
| `add_aggregate` | 按 dimensions 分组并聚合 measures |
| `add_pivot` | 行转列 |
| `add_unpivot` | 列转行 |
| `add_output_server` | 添加 Tableau Server output node |

### Calculation Syntax Notes

Tableau Prep calculation syntax 不是 SQL syntax。常见差异：

| SQL habit | Tableau Prep form |
|---|---|
| `[f] IN ('A','B')` | `[f] = 'A' OR [f] = 'B'` |
| `[f] != 'x'` | `[f] <> 'x'` |
| `[f] BETWEEN 1 AND 5` | `[f] >= 1 AND [f] <= 5` |
| `[f] = "text"` | `[f] = 'text'` |
| `[f] = NULL` | `ISNULL([f])` |

使用 MCP 时，创建公式前先读取 `cwprep://docs/calculation-syntax`。

## CLI Reference

`cwprep` 命令是智能入口：

```text
interactive terminal -> print help
piped MCP stdio      -> start MCP server
```

需要确定行为时，使用显式命令：

```bash
cwprep mcp
cwprep doctor
cwprep status
cwprep capabilities --json
cwprep validate examples/basic_flow.yaml --json
cwprep run examples/basic_flow.yaml --out demo_output/cli_basic_flow.tfl
cwprep run examples/basic_flow.yaml --dry-run
cwprep translate examples/basic_flow.yaml --out demo_output/cli_basic_flow.sql
cwprep translate-tfl demo_output/cli_basic_flow.tfl --out demo_output/from_tfl.sql
```

`CWPREP_MODE=mcp` 强制无参数 `cwprep` 启动 MCP。`CWPREP_MODE=cli` 强制无参数 `cwprep` 打印 CLI 帮助。

Spec 文件使用与 MCP tools 相同的声明式结构：

```yaml
flow_name: CLI Basic Flow
connection:
  host: localhost
  username: root
  dbname: test_db
nodes:
  - type: input_sql
    name: Orders
    sql: SELECT * FROM orders
  - type: output_server
    name: Output
    parent: Orders
    datasource_name: CLI_Basic_Output
output_path: demo_output/cli_basic_flow.tfl
```

## MCP Reference

### MCP Tools

| Tool | Description |
|---|---|
| `generate_tfl` | 从声明式 flow definition 生成 `.tfl` 或 `.tflx` 文件 |
| `translate_to_sql` | 把 flow definition 或 `.tfl` 文件转译为 ANSI SQL |
| `list_supported_operations` | 列出支持的 node types 和 operation names |
| `validate_flow_definition` | 生成前验证 flow definition |

推荐 Agent 工作流：

```text
read resources -> design -> validate_flow_definition -> generate_tfl
```

### MCP Resources

| Resource | Description |
|---|---|
| `cwprep://docs/api-reference` | SDK 和 MCP API reference |
| `cwprep://docs/calculation-syntax` | Tableau Prep calculation syntax |
| `cwprep://docs/best-practices` | 常见坑和 flow design rules |

### MCP Prompts

| Prompt | Description |
|---|---|
| `design_data_flow` | 交互式 flow design assistant |
| `explain_tfl_structure` | TFL 文件结构说明 |

### Client Configuration

以下客户端都使用短命令 `uvx cwprep`。等价显式形式包括 `cwprep mcp`、`uvx --from cwprep cwprep-mcp`、`cwprep-mcp` 和 `python -m cwprep.mcp_server`。

#### Claude Desktop

编辑配置文件：

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

Settings -> MCP -> Add new MCP server，或编辑 `~/.cursor/mcp.json`：

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

在项目根目录创建 `.vscode/mcp.json`：

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

编辑 `~/.gemini/settings.json`：

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

编辑 `~/.continue/config.yaml`：

```yaml
mcpServers:
  - name: cwprep
    command: uvx
    args:
      - cwprep
```

#### Remote HTTP Mode

启动 server：

```bash
cwprep-mcp --transport streamable-http --port 8000
```

然后在客户端中配置 endpoint：

```text
http://your-server-ip:8000/mcp
```

## Configuration

创建 `config.yaml` 配置默认值：

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

SQL Server 和 PostgreSQL 也支持：

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

`examples/` 目录包含基于 Sample Superstore 数据集的完整 demos。

| Script | What it demonstrates |
|---|---|
| `examples/quick_start.py` | 最小 connect、join、filter、calculate、output 工作流 |
| `examples/demo_basic.py` | Input、join、output |
| `examples/demo_cleaning.py` | Filter、value filter、keep only、rename、calculation、remove columns |
| `examples/demo_field_operations.py` | Quick clean、type change、duplicate column |
| `examples/demo_aggregation.py` | Union、aggregate、pivot、unpivot |
| `examples/demo_comprehensive.py` | 端到端 sales analysis flow |
| `examples/demo_mcp_flow.py` | 带生成样例数据的 MCP-friendly review demo |
| `examples/prompts.md` | AI-driven flow generation 的 prompt templates |

运行示例：

```bash
python examples/quick_start.py
```

用 Tableau Prep Builder 打开生成的 `.tfl` 或 `.tflx` 文件检查结果。

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

### 本地开发

```bash
pip install -e ".[dev]"
pytest
python examples/quick_start.py
cwprep
```
