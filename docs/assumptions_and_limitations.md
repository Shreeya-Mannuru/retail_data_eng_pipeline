# Assumptions and Limitations — Retail Data Engineering Pipeline

This document outlines the assumptions made during the design of this pipeline and the known limitations of the current implementation. Understanding these is essential for correctly interpreting the outputs and for planning a production-grade version of this system.

---

## Assumptions

### Data Source
- DummyJSON (https://dummyjson.com) was used as the data source. It is a synthetic API that returns fixed, fictional data. The data does not represent real customers, real products, or real transactions.
- The API returns consistent data on every call — there is no new data arriving over time. This makes it suitable for a portfolio pipeline but not for simulating a real production ingestion scenario.

### Recency Proxy
- DummyJSON provides no date or timestamp fields for carts or orders. `max_cart_id` was used as a proxy for recency under the assumption that cart IDs are assigned sequentially and higher IDs correspond to more recent activity.
- This assumption may not hold in all systems (cart IDs are not always sequential) but is reasonable for this dataset given no alternative exists.

### Currency
- All prices in the DummyJSON API are returned in USD. No currency conversion was applied. Monetary values in the pipeline and dashboard are treated as-is. In a production Indian retail context, INR conversion would be applied at the transformation layer.

### Segment Thresholds
- RFM segment thresholds (score cutoffs for Champions, Loyal Customers, At Risk, Lost Customers) were defined based on standard industry practice and adjusted for the small dataset size (45 customers). Different thresholds may produce different segment distributions.

### One-to-Many Cart Relationship
- A single user can have multiple carts. Each cart can contain multiple products. The pipeline correctly flattens this nested structure into atomic line items (one row per product per cart) before loading into the database.

---

## Known Limitations

### Dataset Size
The DummyJSON API returns a maximum of 100 users, 100 products, and 50 carts — resulting in 45 unique customers with purchase history and 198 cart line items after flattening. This is sufficient for demonstrating pipeline logic and segmentation methodology but is not representative of real retail data volumes, which typically run into millions of transactions.

### No Real Timestamps
Because DummyJSON has no date fields, time-based analysis (true recency in days, purchase trends over time, cohort analysis by month) is not possible with this dataset. `max_cart_id` is used as a directional proxy only.

### SQLite vs Production Databases
SQLite is a file-based, single-user database. It is appropriate for a portfolio prototype but has the following limitations in a production context:
- Cannot handle concurrent writes from multiple processes
- Not suitable for datasets larger than a few GB
- No built-in user access control or role-based permissions
- Not cloud-native — cannot integrate directly with modern data stack tools

In production, this would be replaced with PostgreSQL (for OLTP) or Snowflake / BigQuery / Redshift (for OLAP analytical workloads).

### No Pipeline Orchestration
The three scripts (`extract.py`, `transform.py`, `load.py`) are run manually in sequence. There is no automated scheduling, dependency management, failure alerting, or retry logic. In production, these would be managed by an orchestration tool such as Apache Airflow or Prefect.

### No Streaming
The pipeline runs as a one-time batch process. It does not handle continuously arriving data (new orders, returns, cancellations, inventory updates). A production retail pipeline would typically run on a scheduled batch cadence (hourly or daily) or use a streaming framework like Apache Kafka for real-time ingestion.

### Limited Data Quality Checks
`transform.py` validates for null values but does not perform:
- Referential integrity checks (does every `user_id` in carts exist in users?)
- Duplicate detection
- Value range validation (no negative prices, no quantities below 1)
- Schema drift detection (API response structure changing unexpectedly)

In production, a data quality framework such as Great Expectations or dbt tests would handle these checks automatically.

### Segmentation Method Difference
The SQL (NTILE) and Python (qcut) segmentation approaches produce slightly different segment counts. This is expected — the two methods handle ties and skewed distributions differently. Both outputs are analytically valid. See `docs/rfm_methodology.md` for a full explanation.

---

## What a Production Version Would Include

| Current (Portfolio) | Production Equivalent |
|---|---|
| DummyJSON API | Live POS system, Shopify API, ERP exports |
| Manual script execution | Apache Airflow DAG with scheduling and alerting |
| SQLite | Snowflake / BigQuery / Redshift |
| pandas + SQL transforms | dbt models with lineage and automated testing |
| max_cart_id as recency proxy | Actual purchase_date timestamps |
| 45 customers | Millions of customer records |
| Power BI on static data | Live-connected Tableau or Looker dashboard |
| No data quality framework | Great Expectations or dbt tests on every model |