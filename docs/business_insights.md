# Business Insights — Retail Customer Segmentation

**Project:** Retail Data Engineering Pipeline with RFM Customer Segmentation  
**Data source:** DummyJSON API (mock retail dataset — 45 customers, 50 carts, 198 line items)  
**Segmentation method:** RFM scoring using SQL NTILE(5) window function  
**Dashboard:** `dashboard/Retail_Customer_Segmentation_Dashboard.pbix`

---

## What is RFM Segmentation?

RFM is a customer behaviour framework used widely in retail analytics. It scores each customer across three dimensions:

- **Recency** — How recently did they purchase? (Proxy: max cart ID, since the dataset has no real dates)
- **Frequency** — How many times did they purchase?
- **Monetary** — How much total revenue did they generate?

Each dimension is scored 1–5 using SQL's `NTILE(5)` window function. Scores are combined into a composite RFM score, which is then used to assign each customer to a named segment. This pipeline produced four segments across 45 customers.

---

## Segment Breakdown and Business Implications

### 1. Champions — 7 customers | ₹7,43,122 revenue

Champions are the highest-value customers — high recency, high frequency, high spend. Despite being only **15% of the customer base**, they account for approximately **74% of total revenue**. This is a textbook Pareto distribution.

**What this means for the business:**
- These customers are already highly engaged and profitable. The risk is taking them for granted.
- Priority action: **retention and reward**. Champions should receive early access to new products, exclusive loyalty benefits, or personalised outreach. Losing even two or three of them would materially impact revenue.
- They are also the most credible source of referrals and word-of-mouth. A referral programme targeted at Champions is likely to yield high-quality new customers.

---

### 2. Loyal Customers — 11 customers | ₹1,68,798 revenue

Loyal customers purchase regularly and have a solid spend history, but have not yet reached the high monetary value of Champions. They represent the most actionable **growth opportunity** in the customer base.

**What this means for the business:**
- These customers are close to Champion-tier. A targeted upsell or cross-sell nudge — especially in high-margin product categories — could move them up.
- Priority action: **upgrade and deepen**. Personalised product recommendations based on their purchase history, bundle offers, or a "just for you" promotion campaign are likely to be effective.
- They are significantly lower-risk to engage than cold acquisition. Retaining and upgrading a Loyal Customer is cheaper and more predictable than acquiring a new one.

---

### 3. At Risk — 21 customers | ₹89,876 revenue

At Risk is the largest segment by customer count — **47% of the base** — but contributes only 9% of total revenue. These customers have either low recency (haven't purchased recently) or low frequency relative to their spend.

**What this means for the business:**
- This is the most urgent intervention target. A large share of the customer base is disengaging.
- Priority action: **win-back campaigns**. Re-engagement emails, time-limited discount offers, or a "we miss you" outreach sequence are standard approaches here.
- Not all At Risk customers are worth equal effort. A sub-segmentation by monetary score is recommended — focus win-back spend on At Risk customers with historically higher spend.
- If no action is taken, many of these customers will transition to Lost.

---

### 4. Lost Customers — 6 customers | ₹2,472 revenue

Lost customers have the lowest recency, frequency, and monetary scores. They have largely disengaged from the platform. Revenue contribution is negligible.

**What this means for the business:**
- Heavy re-engagement spend on this segment is unlikely to yield positive ROI.
- Priority action: **low-cost re-activation or exit**. A single automated re-engagement email (low cost) is reasonable. If there is no response, marketing budget should be reallocated toward Champions and Loyal Customers.
- Tracking how customers move *into* this segment over time (i.e., which segment they came from) would help identify where the customer journey is breaking down.

---

## Cross-Segment Observations

### Revenue concentration is high — and a risk

74% of revenue from 15% of customers is efficient in the short term but structurally fragile. If Champions churn — due to a competitor offer, service issue, or natural lifecycle — the revenue impact is disproportionate. The business should treat Champion retention as a **critical operational priority**, not just a marketing exercise.

### The At Risk cohort represents recoverable value

At 21 customers, the At Risk segment is large enough that even a 30% win-back rate (6–7 customers re-engaged) could meaningfully shift revenue distribution. A structured win-back programme with A/B tested messaging is a low-risk, measurable intervention.

### Discount patterns warrant attention

EDA analysis (see `notebooks/eda.ipynb`) shows that discount percentage varies across product categories. There is a risk that heavy discounting is contributing to purchase frequency in lower-value segments without building genuine loyalty. A discount effectiveness analysis — revenue per customer vs. discount received — is recommended before expanding discount-led campaigns.

---

## Recommended Business Actions (Priority Order)

| Priority | Segment | Action | Expected Outcome |
|---|---|---|---|
| 1 | Champions | Loyalty reward programme, early access offers | Reduce churn risk, activate referrals |
| 2 | At Risk | Automated win-back email sequence, time-limited offer | Recover 20–30% of disengaged customers |
| 3 | Loyal Customers | Personalised upsell / cross-sell campaign | Upgrade a portion to Champion tier |
| 4 | Lost Customers | Single re-engagement email, then reallocation | Minimise sunk cost, focus budget elsewhere |

---

## Caveats and Data Limitations

These insights are derived from a **mock dataset** (DummyJSON API) and should not be used to drive real business decisions. Key limitations:

- **No real dates**: Recency was approximated using `max_cart_id` as a proxy. In a production dataset with actual transaction timestamps, recency scoring would be significantly more accurate.
- **Small sample**: 45 customers is too small to draw statistically robust conclusions. Segment behaviour in a real retail dataset of thousands of customers may differ substantially.
- **Single time period**: RFM analysis is most powerful when run across multiple time windows (e.g., comparing this quarter vs. last quarter). This pipeline captures a single snapshot.
- **No product return data**: Customer lifetime value and true monetary score should ideally account for returns and refunds, which are absent from this dataset.

In a production environment, this pipeline would be extended with a proper date dimension, larger transaction volume, incremental data loads, and orchestration via a workflow tool such as Apache Airflow.

---

*Document prepared as part of the retail data engineering pipeline portfolio project.*  
*Author: Shreeya Mannuru | [GitHub](https://github.com/Shreeya-Mannuru/retail_data_eng_pipeline)*
