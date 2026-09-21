import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import duckdb
import pandas as pd

DB_PATH = "c:/Users/ub02-glab-055/Downloads/data/annapurna.duckdb"

def build_star_schema():
    print("="*85)
    print("BUILDING DIMENSIONAL STAR SCHEMA (DuckDB + MinIO + PostgreSQL)")
    print("="*85)
    
    con = duckdb.connect(DB_PATH)
    
    # 1. Extensions
    print("[1/5] Loading httpfs and postgres extensions...")
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute("INSTALL postgres; LOAD postgres;")
    
    # 2. Configure MinIO
    con.execute("""
        CREATE SECRET IF NOT EXISTS minio_secret (
            TYPE S3,
            KEY_ID 'admin',
            SECRET 'admin12345',
            ENDPOINT 'localhost:9000',
            URL_STYLE 'path',
            USE_SSL false
        );
    """)
    
    # 3. Attach PostgreSQL
    print("[2/5] Attaching to PostgreSQL operational database...")
    try:
        con.execute("ATTACH 'host=localhost port=5432 dbname=annapurna_dw user=annapurna password=annapurna123' AS pg (TYPE postgres);")
    except Exception as e:
        pass
        
    # 4. Create dimensions
    print("[3/5] Creating dimensions: dim_store, dim_product, dim_date...")
    con.execute("""
        CREATE OR REPLACE TABLE dim_store AS
        SELECT store_id, store_name, city, state FROM pg.public.stores;
    """)
    
    con.execute("""
        CREATE OR REPLACE TABLE dim_product AS
        SELECT product_sk, product_code, product_name, category, valid_from, valid_to 
        FROM pg.public.products;
    """)
    
    con.execute("""
        DELETE FROM dim_product WHERE product_sk = 0;
        INSERT INTO dim_product (product_sk, product_code, product_name, category, valid_from, valid_to)
        VALUES (0, 'DISCOUNT', 'Bill-Level Discount', 'Promotions & Discounts', '2024-01-01', '2099-12-31');
    """)
    
    con.execute("""
        CREATE OR REPLACE TABLE dim_date AS
        SELECT 
            CAST(d AS DATE) AS date_key,
            YEAR(CAST(d AS DATE)) AS year,
            MONTH(CAST(d AS DATE)) AS month,
            MONTHNAME(CAST(d AS DATE)) AS month_name,
            DAY(CAST(d AS DATE)) AS day,
            DAYNAME(CAST(d AS DATE)) AS day_of_week,
            CASE WHEN DAYNAME(CAST(d AS DATE)) IN ('Saturday', 'Sunday') THEN true ELSE false END AS is_weekend
        FROM generate_series(
            DATE '2024-01-01',
            DATE '2024-12-31',
            INTERVAL 1 DAY
        ) t(d);
    """)
    
    # 5. Create fact table
    print("[4/5] Creating fact_sales (filtering revenue lines & joining SCD-2 product keys)...")
    con.execute("""
        CREATE OR REPLACE TABLE fact_sales AS
        SELECT 
            s.bill_no,
            s.line_no,
            s.store_id,
            COALESCE(p.product_sk, 0) AS product_sk,
            s.business_date AS date_key,
            s.qty AS quantity,
            s.unit_price,
            ROUND(s.qty * s.unit_price, 2) AS net_amount,
            s.line_type
        FROM read_parquet('s3://annapurna-lake/year=*/month=*/store=*/*.parquet') s
        LEFT JOIN dim_product p 
            ON s.product_code = p.product_code 
            AND s.business_date BETWEEN p.valid_from AND p.valid_to
        WHERE s.line_type IN ('SALE', 'RETURN', 'DISCOUNT', 'VOID');
    """)
    
    print("[5/5] Star Schema Build Complete! Fetching table counts...")
    
    counts = con.execute("""
        SELECT 'dim_store' AS table_name, 'Store Dimension (12 Supermarkets)' AS description, count(*) AS row_count FROM dim_store
        UNION ALL
        SELECT 'dim_product', 'Product Dimension (1224 master products + discount key)', count(*) FROM dim_product
        UNION ALL
        SELECT 'dim_date', 'Date Dimension (2024 Leap Year Calendar)', count(*) FROM dim_date
        UNION ALL
        SELECT 'fact_sales', 'Sales Fact Table (Filtered Revenue Lines)', count(*) FROM fact_sales
    """).df()
    
    print("\n" + "="*85)
    print("TASK C2 EVIDENCE: FINAL STAR SCHEMA TABLES & ROW COUNTS")
    print("="*85)
    print(f"{'Table Name':<15} | {'Description':<48} | {'Row Count':>12}")
    print("-" * 85)
    for idx, row in counts.iterrows():
        print(f"{row['table_name']:<15} | {row['description']:<48} | {row['row_count']:>12,}")
    print("-" * 85)
    
    con.close()

if __name__ == "__main__":
    build_star_schema()
