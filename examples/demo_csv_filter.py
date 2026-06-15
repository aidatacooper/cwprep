"""
cwprep CSV Demo: Filter + Aggregation

Business Scenario: Filter orders to Office Supplies only,
then aggregate sales by Sub-Category.

Features Covered:
1. add_file_connection - File-based connection
2. add_input_csv - CSV input node
3. add_filter - Row filter
4. add_aggregate - Group-by aggregation
5. add_output_server - Publish to Tableau Server

Usage:
    python examples/demo_csv_filter.py
"""
import os
from cwprep import TFLBuilder, TFLPackager

# Path to the sample CSV (relative to examples/ folder)
CSV_PATH = os.path.join(os.path.dirname(__file__), "demo_data", "Sample - Superstore_Orders.csv")


def run_csv_filter_demo():
    print("=" * 50)
    print("cwprep CSV Demo: Filter + Aggregation")
    print("=" * 50)
    print()

    # 1. Create builder and file connection
    builder = TFLBuilder(flow_name="Office Supplies Sub-Category Sales")
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

    # 3. Filter to Office Supplies only
    filter_id = builder.add_filter(
        name="Office Supplies Only",
        parent_id=csv_id,
        expression='[Category] = "Office Supplies"',
    )
    print(f"[OK] Add filter: {filter_id[:8]}...")

    # 4. Aggregate sales by Sub-Category
    agg_id = builder.add_aggregate(
        name="Sales by Sub-Category",
        parent_id=filter_id,
        group_by=["Sub-Category"],
        aggregations=[
            {"field": "Sales", "function": "SUM", "output_name": "Total Sales"},
        ],
    )
    print(f"[OK] Add aggregate: {agg_id[:8]}...")

    # 5. Add output
    out_id = builder.add_output_server(
        name="Output",
        parent_id=agg_id,
        datasource_name="Office_Supplies_SubCategory_Sales",
    )
    print(f"[OK] Add output: {out_id[:8]}...")

    # 6. Build and save
    print()
    flow, display, meta = builder.build()
    output_tfl = "./demo_output/csv_filter_aggregation.tfl"
    TFLPackager.save_tfl(output_tfl, flow, display, meta)

    print(f"[OK] Generated: {output_tfl}")
    print()
    print("Data flow: CSV -> Filter -> Aggregate -> Output")


if __name__ == "__main__":
    run_csv_filter_demo()
