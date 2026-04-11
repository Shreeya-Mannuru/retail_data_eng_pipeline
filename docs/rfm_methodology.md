# RFM Methodology — Retail Data Engineering Pipeline

This document explains the RFM segmentation logic used in this project: what RFM is, how scores were calculated, why two approaches were used, and how segments were assigned.

---

## What is RFM?

RFM stands for Recency, Frequency, and Monetary value. It is a customer segmentation framework widely used in retail to rank customers by their purchasing behaviour.

| Dimension | Question it answers | Column used in this project |
|---|---|---|
| Recency | How recently did this customer buy? | `max_cart_id` (proxy) |
| Frequency | How often does this customer buy? | `purchase_count` |
| Monetary | How much has this customer spent? | `total_spent` |

Each customer receives a score of 1 to 5 on each dimension. These three scores are combined to assign the customer to a segment.

---

## Recency Proxy — Why max_cart_id?

The DummyJSON API does not provide any date or timestamp fields for orders or carts. In a real retail dataset, recency would be calculated as the number of days since the customer's last purchase.

Since no date field exists, `max_cart_id` was used as a substitute. The assumption is that cart IDs are assigned sequentially — a higher cart ID indicates a more recent transaction. This is a known limitation of the dataset, not a flaw in the pipeline design.

In a production system, this would be replaced with:
```sql
DATEDIFF(CURRENT_DATE, MAX(purchase_date)) AS recency_days
```

---

## Approach 1 — SQL with NTILE(5) Window Function

### How it works

The SQL approach uses the `NTILE(5)` window function to divide all customers into 5 equal-sized buckets based on their rank on each RFM dimension.

```sql
NTILE(5) OVER (ORDER BY max_cart_id DESC) AS recency_score,
NTILE(5) OVER (ORDER BY purchase_count DESC) AS frequency_score,
NTILE(5) OVER (ORDER BY total_spent DESC) AS monetary_score
```

Score of 5 = best (most recent, most frequent, highest spend).
Score of 1 = worst.

### Why NTILE?

- Produces equal-sized buckets regardless of data distribution
- Is a standard SQL window function — demonstrates SQL fluency
- Easy to schedule and re-run on new data without changing thresholds
- Portable across any SQL-compatible database

### Segment assignment in SQL

After scoring, a composite RFM score is calculated and customers are assigned to segments using a CASE statement:

```sql
CASE
  WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'Champions'
  WHEN frequency_score >= 3 AND monetary_score >= 3 THEN 'Loyal Customers'
  WHEN recency_score <= 2 AND frequency_score >= 2 THEN 'At Risk'
  ELSE 'Lost Customers'
END AS segment
```

---

## Approach 2 — Python with pandas qcut

### How it works

The Python approach uses `pandas.qcut()` to divide customers into quantile-based bins on each RFM dimension, then assigns scores and applies threshold-based segment logic.

```python
df['recency_score'] = pd.qcut(df['max_cart_id'], q=5, labels=[1,2,3,4,5])
df['frequency_score'] = pd.qcut(df['purchase_count'], q=5, labels=[1,2,3,4,5])
df['monetary_score'] = pd.qcut(df['total_spent'], q=5, labels=[1,2,3,4,5])
```

### Why qcut?

- Handles skewed distributions more gracefully than NTILE
- Useful when data is not evenly distributed across the range
- Integrates naturally into a Python-based EDA workflow
- Allows rapid experimentation with different thresholds

### Difference from NTILE

Both methods divide customers into 5 score buckets, but they handle ties and skewed distributions differently. `NTILE` always produces equal-count buckets. `qcut` produces equal-probability buckets but may result in slightly unequal counts when there are duplicate values or heavy skew. This explains why segment counts differ slightly between the SQL and Python outputs — both are valid and expected.

---

## Segment Definitions and Business Meaning

| Segment | Criteria | Count | Total Revenue | Business Action |
|---|---|---|---|---|
| Champions | High R, high F, high M | 7 | ₹7,43,122 | VIP treatment, early access, retention focus |
| Loyal Customers | Medium-high F and M | 11 | ₹1,68,798 | Upsell, increase frequency, move toward Champions |
| At Risk | Low R, medium F | 21 | ₹89,876 | Win-back campaign, personalised discount |
| Lost Customers | Low R, low F, low M | 6 | ₹2,472 | Low-cost automated re-engagement or deprioritise |

---

## Key Finding

7 Champions (15% of customers) generated ₹7,43,122 — approximately 74% of total revenue. This is a textbook demonstration of the Pareto principle in customer analytics: a small fraction of customers drives the majority of value.

---

## Limitations

- Recency is approximated using `max_cart_id`, not actual purchase dates
- Dataset contains only 45 customers — a production RFM model would run on millions of records
- Segment thresholds were chosen based on standard RFM practice and adjusted for this dataset size
- Both SQL and Python approaches produce slightly different counts due to methodological differences — this is expected and both are analytically valid