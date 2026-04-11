# Data Dictionary — Retail Data Engineering Pipeline

This document describes every table and column in the SQLite database (`retail_pipeline.db`) produced by the pipeline.

---

## Table: customers (customer_summary)

Produced by: `transform.py` and `rfm_queries.sql`
One row per customer. Contains aggregated purchase behaviour and RFM segment.

| Column | Data Type | Description | Example |
|---|---|---|---|
| user_id | INTEGER | Unique identifier for each customer. Primary key. | 1 |
| total_spent | REAL | Total amount spent by the customer across all carts. In Indian Rupees (₹). | 43250.75 |
| purchase_count | INTEGER | Number of carts (transactions) associated with this customer. Equivalent to purchase frequency. | 3 |
| max_cart_id | INTEGER | The highest cart ID associated with this customer. Used as a proxy for recency since DummyJSON provides no timestamp fields. Higher value = more recent activity. | 47 |
| segment | TEXT | RFM segment assigned to the customer. One of: Champions, Loyal Customers, At Risk, Lost Customers. | Champions |

---

## Table: carts

Produced by: `transform.py`
One row per product line item per cart. Nested cart data from the DummyJSON API is flattened into this structure.

| Column | Data Type | Description | Example |
|---|---|---|---|
| cart_id | INTEGER | Unique identifier for each cart (transaction). | 12 |
| user_id | INTEGER | Foreign key linking to the customers table. | 5 |
| product_id | INTEGER | Unique identifier for the product purchased. Foreign key linking to products table. | 88 |
| product_title | TEXT | Name of the product as returned by the DummyJSON API. | Wireless Headphones Pro |
| price | REAL | Original unit price of the product before discount. In USD as returned by API. | 149.99 |
| quantity | INTEGER | Number of units of this product purchased in this cart. | 2 |
| total | REAL | Total price before discount (price × quantity). | 299.98 |
| discount_pct | REAL | Percentage discount applied to this line item. | 15.0 |
| discounted_total | REAL | Final amount paid after discount applied. | 254.98 |

---

## Table: products

Produced by: `transform.py`
One row per product. Contains product catalogue information from the DummyJSON API.

| Column | Data Type | Description | Example |
|---|---|---|---|
| product_id | INTEGER | Unique identifier for the product. Primary key. | 88 |
| title | TEXT | Product name. | Wireless Headphones Pro |
| category | TEXT | Product category as classified by DummyJSON. | electronics |
| price | REAL | Listed price of the product. In USD. | 149.99 |
| stock | INTEGER | Number of units available in inventory at time of extraction. | 243 |
| rating | REAL | Average customer rating on a scale of 1 to 5. | 4.3 |
| brand | TEXT | Brand name of the product. May be null for some entries. | SoundMax |

---

## Table: users

Produced by: `transform.py`
One row per user. Contains basic customer profile information from the DummyJSON API.

| Column | Data Type | Description | Example |
|---|---|---|---|
| user_id | INTEGER | Unique identifier for the user. Primary key. | 5 |
| first_name | TEXT | Customer first name. | Priya |
| last_name | TEXT | Customer last name. | Sharma |
| email | TEXT | Customer email address. | priya.sharma@example.com |
| age | INTEGER | Customer age in years. | 29 |
| city | TEXT | City of residence. | Mumbai |

---

## Notes

- Currency: The DummyJSON API returns prices in USD. No currency conversion was applied in this pipeline. All monetary values in the `carts` table are in USD. The `total_spent` in `customer_summary` is also aggregated in USD.
- Recency proxy: DummyJSON does not provide order timestamps or purchase dates. `max_cart_id` is used as a recency proxy on the assumption that higher cart IDs correspond to more recent transactions. This is a known limitation.
- Data volume: 100 products, 100 users, 50 carts, 198 cart line items after flattening.