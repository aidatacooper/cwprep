"""
cwprep Orders-only Demo: Input, Filter, Keep, Output

Business Scenario: High-Value Orders Review
- Connect to the orders table
- Filter high-value orders
- Keep a small set of business fields

Usage:
    python examples/demo_orders_only.py
"""

from cwprep import TFLBuilder, TFLPackager


DB_CONFIG = {
    "host": "localhost",
    "username": "root",
    "dbname": "superstore",
    "port": "3306",
}


def run_orders_only_demo():
    print("=" * 50)
    print("cwprep Orders-only Demo: High-Value Orders")
    print("=" * 50)
    print()

    builder = TFLBuilder(flow_name="High-Value Orders Review")
    conn_id = builder.add_connection(**DB_CONFIG)
    print(f"[OK] Add database connection: {conn_id[:8]}...")

    orders_id = builder.add_input_sql(
        name="Orders",
        sql="""SELECT
order_id,
order_date,
ship_date,
ship_mode,
customer_id,
customer_name,
segment,
region,
category,
sub_category,
product_name,
sales,
quantity,
discount,
profit
FROM orders""",
        connection_id=conn_id,
    )
    print(f"[OK] Add orders table: {orders_id[:8]}...")

    filter_id = builder.add_filter(
        name="Filter High-Value Orders",
        parent_id=orders_id,
        expression="[sales] > 500",
    )
    print(f"[OK] Filter orders: sales > 500")

    keep_id = builder.add_keep_only(
        name="Keep Review Fields",
        parent_id=filter_id,
        columns=[
            "order_id",
            "order_date",
            "customer_name",
            "segment",
            "region",
            "category",
            "product_name",
            "sales",
            "profit",
        ],
    )
    print(f"[OK] Keep review fields")

    output_id = builder.add_output_server(
        name="High-Value Orders Output",
        parent_id=keep_id,
        datasource_name="High_Value_Orders",
    )
    print(f"[OK] Add output: {output_id[:8]}...")

    print()
    flow, display, meta = builder.build()
    output_tfl = "./demo_output/orders_only.tfl"

    TFLPackager.save_tfl(output_tfl, flow, display, meta)

    print(f"[OK] Generated: {output_tfl}")
    print()
    print("Data flow: Orders -> Filter sales > 500 -> Keep fields -> Output")


if __name__ == "__main__":
    run_orders_only_demo()
