"""
cwprep CSV Demo: Sales by Category

Business Scenario: Read a local CSV file and aggregate sales by category.

Features Covered:
1. add_file_connection - File-based connection
2. add_input_csv - CSV input node
3. add_aggregate - Group-by aggregation
4. add_output_server - Publish to Tableau Server

Usage:
    python examples/demo_csv_aggregation.py
"""
import os
from cwprep import TFLBuilder, TFLPackager

# Path to the sample CSV (relative to examples/ folder)
CSV_PATH = os.path.join(os.path.dirname(__file__), "demo_data", "Sample - Superstore_Orders.csv")


def run_csv_aggregation_demo():
    print("=" * 50)
    print("cwprep CSV Demo: Sales by Category")
    print("=" * 50)
    print()

    # 1. Create builder and file connection
    builder = TFLBuilder(flow_name="Sales by Category")
    conn_id = builder.add_file_connection(CSV_PATH)
    print(f"[OK] Add file connection: {conn_id[:8]}...")

    # 2. Add CSV input node
    csv_id = builder.add_input_csv(
        name="Orders CSV",
        connection_id=conn_id,
        fields=[
            {"name": "Category", "type": "string"},
            {"name": "Order Date", "type": "date"},
            {"name": "Sub-Category", "type": "string"},
            {"name": "Sales", "type": "real"},
        ],
    )
    print(f"[OK] Add CSV input: {csv_id[:8]}...")

    # 3. Aggregate sales by category
    agg_id = builder.add_aggregate(
        name="Total Sales by Category",
        parent_id=csv_id,
        group_by=["Category"],
        aggregations=[
            {"field": "Sales", "function": "SUM", "output_name": "Total Sales"},
        ],
    )
    print(f"[OK] Add aggregate: {agg_id[:8]}...")

    # 4. Add output
    out_id = builder.add_output_server(
        name="Output",
        parent_id=agg_id,
        datasource_name="Sales_by_Category",
    )
    print(f"[OK] Add output: {out_id[:8]}...")

    # 5. Build and save
    print()
    flow, display, meta = builder.build()
    output_tfl = "./demo_output/csv_sales_by_category.tfl"
    TFLPackager.save_tfl(output_tfl, flow, display, meta)

    print(f"[OK] Generated: {output_tfl}")
    print()
    print("Data flow: CSV -> Aggregate -> Output")


if __name__ == "__main__":
    run_csv_aggregation_demo()
