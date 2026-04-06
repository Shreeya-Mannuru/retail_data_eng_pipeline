import sqlite3
import pandas as pd
import os

# --- Configuration ---
PROCESSED_DIR = "data/processed"
DB_PATH = "data/retail_pipeline.db"

# sqlite3 is a built-in Python library — no pip install needed.
# It lets Python talk to a SQLite database file directly.
# pandas is used to read our processed CSVs before loading them.
# os is used to check if the database file already exists.


def get_connection():
    """
    Creates and returns a connection to the SQLite database.

    sqlite3.connect(DB_PATH) does two things:
    - If the .db file doesn't exist → creates it
    - If it already exists → opens it

    A 'connection' is like opening a phone call to the database.
    Every query you run goes through this connection.
    You must close it when done — like hanging up the call.
    """
    conn = sqlite3.connect(DB_PATH)
    print(f"  ✓ Connected to database: {DB_PATH}")
    return conn


def create_tables(conn):
    """
    Creates the 4 tables in SQLite if they don't already exist.

    conn.cursor() creates a 'cursor' object.
    A cursor is the tool you use to actually execute SQL statements.
    Think of connection as the phone line, cursor as the person speaking.

    cursor.execute() sends one SQL statement to the database.
    
    'IF NOT EXISTS' means: don't crash if the table already exists.
    This makes the script safe to re-run multiple times.

    PRIMARY KEY tells the database this column uniquely identifies each row.
    TEXT, REAL, INTEGER are SQLite data types:
      - TEXT  → strings
      - REAL  → decimal numbers (float)
      - INTEGER → whole numbers
    """
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id  INTEGER PRIMARY KEY,
            title       TEXT,
            category    TEXT,
            price       REAL,
            stock       INTEGER,
            rating      REAL,
            brand       TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            first_name  TEXT,
            last_name   TEXT,
            email       TEXT,
            gender      TEXT,
            age         INTEGER,
            city        TEXT,
            state       TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carts (
            cart_id         INTEGER,
            user_id         INTEGER,
            product_id      INTEGER,
            product_title   TEXT,
            price           REAL,
            quantity        INTEGER,
            total           REAL,
            discount_pct    REAL,
            discounted_total REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_summary (
            user_id         INTEGER PRIMARY KEY,
            total_spent     REAL,
            purchase_count  INTEGER,
            max_cart_id     INTEGER
        )
    """)

    # commit() saves all the CREATE TABLE statements permanently.
    # Without commit(), changes exist only in memory and disappear
    # when the connection closes. Always commit after write operations.
    conn.commit()
    print("  ✓ All 4 tables created (or already exist)")


def load_table(conn, csv_filename, table_name):
    """
    Reads a processed CSV and loads it into a SQLite table.

    pd.read_csv() reads the CSV into a Pandas DataFrame —
    same flat table structure we saved in transform.py.

    df.to_sql() is Pandas' built-in method to write a DataFrame
    directly into a SQL table. Parameters:
      - table_name: which table to write into
      - conn: the database connection to use
      - if_exists='replace': if the table already has data,
        delete it and reload fresh. Alternatives:
          'append' → add rows to existing data
          'fail'   → crash if table already has data
      - index=False: don't write Pandas row numbers as a column

    Why 'replace' and not 'append'?
    Every time we run the pipeline, we want fresh data — not
    duplicates from previous runs stacking up.
    """
    filepath = f"{PROCESSED_DIR}/{csv_filename}"
    df = pd.read_csv(filepath)
    
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    
    print(f"  ✓ Loaded {len(df)} rows into '{table_name}'")


def verify_load(conn):
    """
    Runs a simple COUNT(*) query on each table to confirm data loaded.

    This is called a 'sanity check' — a quick verification that
    what you intended to happen actually happened.

    cursor.fetchone() retrieves exactly one row from the query result.
    COUNT(*) always returns one row (the count), so fetchone() is correct.
    fetchone() returns a tuple — e.g. (100,) — so we take index [0]
    to get just the number.

    In real DE pipelines, this verification step is called
    'data quality assertion' or 'pipeline testing'.
    """
    cursor = conn.cursor()
    
    tables = ["products", "users", "carts", "customer_summary"]
    
    print("\n  Row counts after load:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"    {table}: {count} rows")


def run_load():
    print("=" * 50)
    print("LOAD LAYER — SQLite")
    print("=" * 50)

    # Step 1: Connect
    print("\n[Connecting]")
    conn = get_connection()

    # Step 2: Create tables
    print("\n[Creating Tables]")
    create_tables(conn)

    # Step 3: Load each CSV into its table
    print("\n[Loading Data]")
    load_table(conn, "products_clean.csv",    "products")
    load_table(conn, "users_clean.csv",       "users")
    load_table(conn, "carts_clean.csv",       "carts")
    load_table(conn, "customer_summary.csv",  "customer_summary")

    # Step 4: Verify
    print("\n[Verification]")
    verify_load(conn)

    # Always close the connection when done.
    # Leaving connections open wastes memory and can cause
    # file lock issues — other processes can't access the db.
    conn.close()
    print("\n  ✓ Connection closed")

    print("\n" + "=" * 50)
    print("✓ Load complete. Database ready for SQL queries.")
    print("=" * 50)


if __name__ == "__main__":
    run_load()