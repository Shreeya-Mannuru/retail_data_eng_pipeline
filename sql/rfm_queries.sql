-- =====================================================
-- RFM SEGMENTATION QUERIES
-- Retail Data Engineering Pipeline
-- =====================================================
-- RFM = Recency, Frequency, Monetary
-- Each customer is scored 1-5 on each dimension
-- Score 5 = best, Score 1 = worst
-- NTILE(5) divides customers into 5 equal buckets
-- =====================================================


-- =====================================================
-- QUERY 1: Basic exploration before RFM
-- Always explore your data before segmenting
-- =====================================================

SELECT 
    COUNT(DISTINCT user_id)     AS total_customers,
    COUNT(*)                    AS total_transactions,
    ROUND(SUM(total), 2)        AS total_revenue,
    ROUND(AVG(total), 2)        AS avg_transaction_value,
    ROUND(MAX(total), 2)        AS max_transaction_value,
    ROUND(MIN(total), 2)        AS min_transaction_value
FROM carts;


-- =====================================================
-- QUERY 2: Revenue by product category
-- Joins carts with products to get category-level view
-- =====================================================

SELECT 
    p.category,
    COUNT(*)                        AS total_transactions,
    ROUND(SUM(c.total), 2)          AS total_revenue,
    ROUND(AVG(c.price), 2)          AS avg_price,
    SUM(c.quantity)                 AS total_units_sold
FROM carts c
-- JOIN connects two tables on a shared column
-- INNER JOIN = only rows that exist in BOTH tables
JOIN products p ON c.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;


-- =====================================================
-- QUERY 3: Top 10 customers by total spend
-- =====================================================

SELECT 
    cs.user_id,
    u.first_name || ' ' || u.last_name   AS customer_name,
    u.city,
    cs.total_spent,
    cs.purchase_count
FROM customer_summary cs
-- LEFT JOIN = all rows from left table (customer_summary)
-- even if no match exists in right table (users)
LEFT JOIN users u ON cs.user_id = u.user_id
ORDER BY cs.total_spent DESC
LIMIT 10;


-- =====================================================
-- QUERY 4: FULL RFM SEGMENTATION
-- This is the core analytical query
-- =====================================================

WITH rfm_base AS (
    -- Step 1: Pull raw R, F, M values per customer
    -- We already have these in customer_summary from transform.py
    -- max_cart_id is our Recency proxy (no real dates in DummyJSON)
    -- Higher cart_id = purchased later = more recent
    SELECT
        cs.user_id,
        u.first_name || ' ' || u.last_name     AS customer_name,
        u.city,
        cs.max_cart_id                          AS recency_raw,
        cs.purchase_count                       AS frequency_raw,
        cs.total_spent                          AS monetary_raw
    FROM customer_summary cs
    LEFT JOIN users u ON cs.user_id = u.user_id
),

rfm_scored AS (
    -- Step 2: Score each dimension using NTILE(5)
    -- NTILE(5) splits all customers into 5 equal buckets
    -- OVER (ORDER BY ...) defines how to rank before bucketing
    -- For Recency: higher cart_id = more recent = better = score 5
    -- For Frequency: more purchases = better = score 5
    -- For Monetary: more spent = better = score 5
    SELECT
        user_id,
        customer_name,
        city,
        recency_raw,
        frequency_raw,
        monetary_raw,
        NTILE(5) OVER (ORDER BY recency_raw ASC)    AS r_score,
        NTILE(5) OVER (ORDER BY frequency_raw ASC)  AS f_score,
        NTILE(5) OVER (ORDER BY monetary_raw ASC)   AS m_score
    FROM rfm_base
),

rfm_combined AS (
    -- Step 3: Combine scores into total and a label string
    -- CAST(x AS TEXT) converts integer to string for concatenation
    -- || is SQLite's string concatenation operator (like + in Python)
    SELECT
        user_id,
        customer_name,
        city,
        recency_raw,
        frequency_raw,
        monetary_raw,
        r_score,
        f_score,
        m_score,
        (r_score + f_score + m_score)                           AS rfm_total,
        CAST(r_score AS TEXT) || CAST(f_score AS TEXT) 
            || CAST(m_score AS TEXT)                            AS rfm_label
    FROM rfm_scored
)

-- Step 4: Final output with segment names
-- CASE WHEN is SQL's if-elif-else
-- We assign business segment labels based on total RFM score
SELECT
    user_id,
    customer_name,
    city,
    ROUND(monetary_raw, 2)      AS total_spent,
    frequency_raw               AS purchase_count,
    r_score,
    f_score,
    m_score,
    rfm_total,
    rfm_label,
    CASE
        WHEN rfm_total >= 13                        THEN 'Champions'
        WHEN rfm_total >= 10 AND rfm_total <= 12    THEN 'Loyal Customers'
        WHEN rfm_total >= 7  AND rfm_total <= 9     THEN 'At Risk'
        ELSE                                             'Lost Customers'
    END AS customer_segment
FROM rfm_combined
ORDER BY rfm_total DESC;


-- =====================================================
-- QUERY 5: Segment summary — how many in each segment?
-- Wrap Query 4 in another CTE to aggregate by segment
-- =====================================================

WITH rfm_base AS (
    SELECT
        cs.user_id,
        cs.max_cart_id      AS recency_raw,
        cs.purchase_count   AS frequency_raw,
        cs.total_spent      AS monetary_raw
    FROM customer_summary cs
),
rfm_scored AS (
    SELECT
        user_id,
        recency_raw,
        frequency_raw,
        monetary_raw,
        NTILE(5) OVER (ORDER BY recency_raw ASC)    AS r_score,
        NTILE(5) OVER (ORDER BY frequency_raw ASC)  AS f_score,
        NTILE(5) OVER (ORDER BY monetary_raw ASC)   AS m_score
    FROM rfm_base
),
rfm_segmented AS (
    SELECT
        user_id,
        monetary_raw,
        (r_score + f_score + m_score) AS rfm_total,
        CASE
            WHEN (r_score + f_score + m_score) >= 13   THEN 'Champions'
            WHEN (r_score + f_score + m_score) >= 10   THEN 'Loyal Customers'
            WHEN (r_score + f_score + m_score) >= 7    THEN 'At Risk'
            ELSE                                             'Lost Customers'
        END AS customer_segment
    FROM rfm_scored
)
SELECT
    customer_segment,
    COUNT(*)                        AS customer_count,
    ROUND(AVG(monetary_raw), 2)     AS avg_spend,
    ROUND(SUM(monetary_raw), 2)     AS total_revenue_contribution
FROM rfm_segmented
GROUP BY customer_segment
ORDER BY avg_spend DESC;