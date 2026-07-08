# Orders-only Superstore Schema

Use this schema for simple cwprep examples that only need the `orders` table.

## Default Database Connection

| Database | Host | Port | User | Password | Database |
|----------|------|------|------|----------|----------|
| MySQL | localhost | 3306 | root | empty | superstore |
| PostgreSQL | localhost | 5432 | postgres | qwer123 | superstore |
| SQL Server | 127.0.0.1 | default | SSPI | SSPI | superstore |

## Table: orders

The table is loaded from the `Orders` sheet in `Sample - Superstore.xls` by running:

```bash
python examples/demo_data/load_orders_only.py --db mysql
```

| Field | Description |
|-------|-------------|
| row_id | Row number from the sample data |
| order_id | Order identifier |
| order_date | Order date |
| ship_date | Ship date |
| ship_mode | Shipping mode |
| customer_id | Customer identifier |
| customer_name | Customer name |
| segment | Customer segment |
| country | Country or region |
| city | City |
| state | State or province |
| postal_code | Postal code |
| region | Sales region |
| product_id | Product identifier |
| category | Product category |
| sub_category | Product sub-category |
| product_name | Product name |
| sales | Sales amount |
| quantity | Quantity sold |
| discount | Discount rate |
| profit | Profit amount |

## Example Query

```sql
SELECT
  order_id,
  order_date,
  customer_name,
  region,
  category,
  product_name,
  sales,
  profit
FROM orders
WHERE sales > 500;
```
