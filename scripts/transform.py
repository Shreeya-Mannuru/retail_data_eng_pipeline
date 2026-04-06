import json
import pandas as pd
import os
import glob

# --- Configuration ---
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

def load_latest_raw(endpoint_name):
    """
    Finds the most recently saved raw JSON file for a given endpoint.
    
    glob.glob() searches for files matching a pattern — like a wildcard search.
    Pattern: "data/raw/products_*.json" matches any products file regardless of timestamp.
    We sort by filename (which starts with timestamp) and take the last one = most recent.
    
    Why not hardcode the filename? Because timestamps make filenames unique.
    This function always picks the latest run automatically.
    """
    pattern = f"{RAW_DIR}/{endpoint_name}_*.json"
    files = glob.glob(pattern)
    
    if not files:
        print(f"  ✗ No raw files found for {endpoint_name}")
        return None
    
    latest_file = sorted(files)[-1]
    print(f"  ✓ Loading: {latest_file}")
    
    with open(latest_file, "r") as f:
        return json.load(f)


def transform_products(raw_data):
    """
    Converts raw products list into a clean flat DataFrame.
    
    A DataFrame is a table structure from the Pandas library —
    rows and columns, exactly like an Excel sheet or a SQL table.
    pd.DataFrame() takes a list of dictionaries and makes a table.
    
    We select only the columns we need — dropping image URLs, descriptions
    etc. that aren't useful for analytics.
    """
    df = pd.DataFrame(raw_data)
    
    # Select only analytically useful columns
    # 'rating' in DummyJSON is a direct float field, not nested
    columns_needed = [
        "id", "title", "category", "price", "stock", "rating", "brand"
    ]
    
    # Some products may not have a brand — .get() handles missing keys
    # We use reindex so missing columns become NaN instead of crashing
    df = df.reindex(columns=columns_needed)
    
    # Rename id to product_id for clarity in SQL joins later
    df = df.rename(columns={"id": "product_id"})
    
    # Validate — check for nulls in critical columns
    null_counts = df[["product_id", "price", "category"]].isnull().sum()
    if null_counts.any():
        print(f"  ⚠ Nulls found in products: {null_counts[null_counts > 0].to_dict()}")
    else:
        print(f"  ✓ Products validated — no nulls in critical columns")
    
    print(f"  ✓ Products transformed: {len(df)} rows")
    return df


def transform_users(raw_data):
    """
    Flattens nested address fields and selects relevant user columns.
    
    The address object is nested inside each user dictionary.
    We extract city and state out of it and add them as direct columns.
    
    A list comprehension [ x for item in list ] is used here to
    build a new list of flat dictionaries from the nested raw data.
    It's more efficient than a for loop for this pattern.
    """
    flat_users = []
    
    for user in raw_data:
        flat_users.append({
            "user_id":    user.get("id"),
            "first_name": user.get("firstName"),
            "last_name":  user.get("lastName"),
            "email":      user.get("email"),
            "gender":     user.get("gender"),
            "age":        user.get("age"),
            "city":       user.get("address", {}).get("city"),
            "state":      user.get("address", {}).get("state"),
        })
    
    df = pd.DataFrame(flat_users)
    
    # Validate
    null_counts = df[["user_id", "email"]].isnull().sum()
    if null_counts.any():
        print(f"  ⚠ Nulls found in users: {null_counts[null_counts > 0].to_dict()}")
    else:
        print(f"  ✓ Users validated — no nulls in critical columns")
    
    print(f"  ✓ Users transformed: {len(df)} rows")
    return df


def transform_carts(raw_data):
    """
    This is the most important transformation — flattening nested carts.
    
    Each cart contains a list of products. We explode this so that
    every product in every cart becomes its own row.
    
    Example:
    Cart 1 has 3 products → becomes 3 rows, all with cart_id=1, user_id=1
    
    This is called a one-to-many relationship:
    One cart → many product rows
    
    Why do we need this flat structure?
    SQL GROUP BY and Power BI both need flat rows to aggregate correctly.
    You cannot SUM quantities from a nested list in SQL.
    """
    flat_rows = []
    
    for cart in raw_data:
        cart_id = cart.get("id")
        user_id = cart.get("userId")
        
        # Each cart has a list of products — loop through each
        for product in cart.get("products", []):
            flat_rows.append({
                "cart_id":            cart_id,
                "user_id":            user_id,
                "product_id":         product.get("id"),
                "product_title":      product.get("title"),
                "price":              product.get("price"),
                "quantity":           product.get("quantity"),
                "total":              product.get("total"),
                "discount_pct":       product.get("discountPercentage"),
                "discounted_total":   product.get("discountedPrice"),
            })
    
    df = pd.DataFrame(flat_rows)
    
    # Validate
    null_counts = df[["cart_id", "user_id", "product_id", "total"]].isnull().sum()
    if null_counts.any():
        print(f"  ⚠ Nulls found in carts: {null_counts[null_counts > 0].to_dict()}")
    else:
        print(f"  ✓ Carts validated — no nulls in critical columns")
    
    print(f"  ✓ Carts flattened: {len(df)} rows (one row per product per cart)")
    return df


def derive_customer_summary(df_carts):
    """
    Derives the RFM-ready customer summary table.
    
    This table doesn't exist in the raw data — we calculate it.
    This is what 'derived columns' means in DE: new analytical columns
    built from existing data using aggregation logic.
    
    groupby("user_id") groups all rows belonging to the same user.
    agg() then applies different aggregation functions to different columns:
      - total → sum (total money spent)
      - cart_id → count (how many purchases = frequency)
    
    We don't have real dates in DummyJSON carts, so we use cart_id
    as a proxy for recency — higher cart_id = more recent purchase.
    We'll note this honestly in the README.
    """
    customer_summary = df_carts.groupby("user_id").agg(
        total_spent    = ("total", "sum"),
        purchase_count = ("cart_id", "nunique"),
        max_cart_id    = ("cart_id", "max")
    ).reset_index()
    
    # Round total_spent to 2 decimal places
    customer_summary["total_spent"] = customer_summary["total_spent"].round(2)
    
    print(f"  ✓ Customer summary derived: {len(customer_summary)} unique customers")
    return customer_summary


def save_processed(df, name):
    """
    Saves a cleaned DataFrame to data/processed/ as CSV.
    
    Why CSV and not JSON?
    Processed data is flat (no nesting), so CSV is the right format.
    CSV loads directly into SQLite, SQL tools, and Power BI with no parsing needed.
    
    index=False tells Pandas not to write the row numbers (0,1,2...)
    as a column in the CSV — we don't need those.
    """
    filepath = f"{PROCESSED_DIR}/{name}.csv"
    df.to_csv(filepath, index=False)
    print(f"  ✓ Saved to {filepath}")


def run_transformation():
    print("=" * 50)
    print("TRANSFORMATION LAYER")
    print("=" * 50)

    # Products
    print("\n[Products]")
    raw_products = load_latest_raw("products")
    df_products = transform_products(raw_products)
    save_processed(df_products, "products_clean")

    # Users
    print("\n[Users]")
    raw_users = load_latest_raw("users")
    df_users = transform_users(raw_users)
    save_processed(df_users, "users_clean")

    # Carts
    print("\n[Carts]")
    raw_carts = load_latest_raw("carts")
    df_carts = transform_carts(raw_carts)
    save_processed(df_carts, "carts_clean")

    # Customer Summary (derived)
    print("\n[Customer Summary — Derived]")
    df_summary = derive_customer_summary(df_carts)
    save_processed(df_summary, "customer_summary")

    print("\n" + "=" * 50)
    print("✓ Transformation complete.")
    print("=" * 50)


if __name__ == "__main__":
    run_transformation()