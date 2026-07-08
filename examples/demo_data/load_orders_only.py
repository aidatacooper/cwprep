"""
Orders-only Superstore Data Loader
Load the Orders sheet from Sample - Superstore.xls into MySQL, PostgreSQL, or SQL Server.

Usage:
    python load_orders_only.py --db mysql
    python load_orders_only.py --db postgresql
    python load_orders_only.py --db sqlserver

    # Override default connection parameters:
    python load_orders_only.py --db mysql --host 127.0.0.1 --port 3306 --user root --password secret
    python load_orders_only.py --db postgresql --host localhost --port 5432 --user postgres --password secret
    python load_orders_only.py --db sqlserver --driver "ODBC+Driver+18+for+SQL+Server"
"""

import argparse
import os
import sys

import pandas as pd
import xlrd
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


DB_DEFAULTS = {
    "mysql": {
        "host": "127.0.0.1",
        "port": "3306",
        "user": "root",
        "password": "",
        "dbname": "superstore",
        "driver": "mysql+pymysql",
    },
    "postgresql": {
        "host": "localhost",
        "port": "5432",
        "user": "postgres",
        "password": "qwer123",
        "dbname": "superstore",
        "driver": "postgresql+psycopg2",
    },
    "sqlserver": {
        "host": "127.0.0.1",
        "port": None,
        "user": None,
        "password": None,
        "dbname": "superstore",
        "driver": "mssql+pyodbc",
        "odbc_driver": "ODBC+Driver+17+for+SQL+Server",
    },
}


def _build_url(cfg: dict, dbname: str | None = None) -> str:
    """Build a SQLAlchemy connection URL from config dict."""
    db = dbname or cfg["dbname"]
    db_type = cfg["_type"]

    if db_type == "sqlserver":
        odbc = cfg.get("odbc_driver", "ODBC+Driver+17+for+SQL+Server")
        if cfg.get("user"):
            return f"{cfg['driver']}://{cfg['user']}:{cfg['password']}@{cfg['host']}/{db}?driver={odbc}"
        return f"{cfg['driver']}://@{cfg['host']}/{db}?driver={odbc}&Trusted_Connection=yes"

    if db_type == "mysql":
        if cfg["password"]:
            return f"{cfg['driver']}://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{db}"
        return f"{cfg['driver']}://{cfg['user']}@{cfg['host']}:{cfg['port']}/{db}"

    return f"{cfg['driver']}://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{db}"


def _prepare_mysql(cfg: dict):
    """Connect to MySQL and clear the orders table if it exists."""
    engine = create_engine(_build_url(cfg))
    with engine.connect() as conn:
        print("Successfully connected to MySQL!")
        print("Clearing existing orders table...")
        conn.execute(text("DROP TABLE IF EXISTS orders;"))
        conn.commit()
    return engine


def _prepare_postgresql(cfg: dict):
    """Connect to PostgreSQL, create database if missing, and clear orders."""
    admin_url = _build_url(cfg, dbname="postgres")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{cfg['dbname']}'")
        ).fetchone()
        if not exists:
            print(f"Database '{cfg['dbname']}' does not exist. Creating...")
            conn.execute(text(f"CREATE DATABASE {cfg['dbname']}"))
            print(f"Database '{cfg['dbname']}' created.")
        else:
            print(f"Database '{cfg['dbname']}' already exists.")

    engine = create_engine(_build_url(cfg))
    with engine.connect() as conn:
        print("Successfully connected to PostgreSQL!")
        print("Clearing existing orders table...")
        conn.execute(text("DROP TABLE IF EXISTS orders CASCADE;"))
        conn.commit()
    return engine


def _prepare_sqlserver(cfg: dict):
    """Connect to SQL Server, create database if missing, and clear orders."""
    master_url = _build_url(cfg, dbname="master")
    master_engine = create_engine(master_url, isolation_level="AUTOCOMMIT")
    with master_engine.connect() as conn:
        result = conn.execute(
            text(f"SELECT name FROM sys.databases WHERE name = '{cfg['dbname']}'")
        ).fetchone()
        if not result:
            print(f"Database '{cfg['dbname']}' does not exist. Creating...")
            conn.execute(text(f"CREATE DATABASE {cfg['dbname']}"))
            print(f"Database '{cfg['dbname']}' created.")
        else:
            print(f"Database '{cfg['dbname']}' already exists.")

    engine = create_engine(_build_url(cfg))
    with engine.connect() as conn:
        print("Successfully connected to SQL Server!")
        print("Clearing existing orders table...")
        conn.execute(text("IF OBJECT_ID('orders', 'U') IS NOT NULL DROP TABLE orders;"))
        conn.commit()
    return engine


_PREPARE_FN = {
    "mysql": _prepare_mysql,
    "postgresql": _prepare_postgresql,
    "sqlserver": _prepare_sqlserver,
}


def _flex_rename(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Rename columns with flexible alias matching (case-insensitive)."""
    cols = {c.lower(): c for c in df.columns}
    new_map = {}
    for target, aliases in mapping.items():
        for alias in aliases:
            if alias.lower() in cols:
                new_map[cols[alias.lower()]] = target
                break
        else:
            print(f"Warning: Could not find column for '{target}' (tried: {aliases})")
    return df.rename(columns=new_map)


def transform_orders(xls_path: str) -> pd.DataFrame:
    """Read the Orders sheet and return a single orders DataFrame."""
    print(f"Reading Excel Orders sheet: {xls_path}")
    workbook = xlrd.open_workbook(xls_path)
    sheet = workbook.sheet_by_name("Orders")
    headers = [str(sheet.cell_value(0, col)).strip() for col in range(sheet.ncols)]
    rows = []
    for row_idx in range(1, sheet.nrows):
        row = []
        for col_idx, header in enumerate(headers):
            cell = sheet.cell(row_idx, col_idx)
            value = cell.value
            if header in ("Order Date", "Ship Date") and cell.ctype == xlrd.XL_CELL_DATE:
                value = xlrd.xldate_as_datetime(value, workbook.datemode).date().isoformat()
            row.append(value)
        rows.append(row)

    df_orders_raw = pd.DataFrame(rows, columns=headers, dtype=object)
    df_orders_raw.columns = df_orders_raw.columns.str.strip()

    order_map = {
        "row_id": ["Row ID"],
        "order_id": ["Order ID"],
        "order_date": ["Order Date"],
        "ship_date": ["Ship Date"],
        "ship_mode": ["Ship Mode"],
        "customer_id": ["Customer ID"],
        "customer_name": ["Customer Name"],
        "segment": ["Segment"],
        "country": ["Country", "Country/Region"],
        "city": ["City"],
        "state": ["State", "State/Province", "Province"],
        "postal_code": ["Postal Code", "Zip Code", "Postcode"],
        "region": ["Region"],
        "product_id": ["Product ID"],
        "category": ["Category"],
        "sub_category": ["Sub-Category", "Sub Category"],
        "product_name": ["Product Name"],
        "sales": ["Sales"],
        "quantity": ["Quantity"],
        "discount": ["Discount"],
        "profit": ["Profit"],
    }

    df_orders = _flex_rename(df_orders_raw.copy(), order_map)
    columns = list(order_map.keys())
    df_orders = df_orders[columns]
    return df_orders


def load_orders(engine, orders: pd.DataFrame, if_exists: str = "replace"):
    """Write the orders DataFrame to the database."""
    orders.to_sql("orders", engine, if_exists=if_exists, index=False)
    print(f"  OK orders: {len(orders)} rows loaded")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Load only the Orders sheet from Sample - Superstore.xls into a local database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python load_orders_only.py --db mysql
  python load_orders_only.py --db postgresql
  python load_orders_only.py --db sqlserver
  python load_orders_only.py --db mysql --host 127.0.0.1 --port 3306 --user root --password mypass
  python load_orders_only.py --db postgresql --host localhost --port 5432 --user myuser --password mypass
  python load_orders_only.py --db sqlserver --driver "ODBC+Driver+18+for+SQL+Server"
        """,
    )
    parser.add_argument(
        "--db", required=True, choices=["mysql", "postgresql", "sqlserver"],
        help="Target database type",
    )
    parser.add_argument("--host", help="Database host (overrides default)")
    parser.add_argument("--port", help="Database port (overrides default)")
    parser.add_argument("--user", help="Database username (overrides default)")
    parser.add_argument("--password", help="Database password (overrides default)")
    parser.add_argument("--dbname", help="Database name (default: superstore)")
    parser.add_argument(
        "--driver",
        help="ODBC driver string for SQL Server (default: ODBC+Driver+17+for+SQL+Server)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    db_type = args.db

    cfg = {**DB_DEFAULTS[db_type], "_type": db_type}
    if args.host:
        cfg["host"] = args.host
    if args.port:
        cfg["port"] = args.port
    if args.user:
        cfg["user"] = args.user
    if args.password:
        cfg["password"] = args.password
    if args.dbname:
        cfg["dbname"] = args.dbname
    if args.driver:
        cfg["odbc_driver"] = args.driver

    xls_path = os.path.join(os.path.dirname(__file__), "Sample - Superstore.xls")
    if not os.path.exists(xls_path):
        print(f"Error: File not found at {xls_path}")
        sys.exit(1)

    print(f"--- Loading Superstore Orders into {db_type.upper()} ---")
    print(f"Target: {cfg.get('user', 'SSPI')}@{cfg['host']}/{cfg['dbname']}")

    try:
        engine = _PREPARE_FN[db_type](cfg)
    except Exception as e:
        print(f"Database preparation failed: {e}")
        sys.exit(1)

    orders = transform_orders(xls_path)
    load_orders(engine, orders)

    print(f"\nOrders-only data loading to {db_type.upper()} completed successfully!")


if __name__ == "__main__":
    main()
