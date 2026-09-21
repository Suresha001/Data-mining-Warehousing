import sys
import duckdb

sys.stdout.reconfigure(encoding='utf-8')

def test_federated():
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute("INSTALL postgres; LOAD postgres;")

    con.execute("""
    CREATE SECRET minio_secret (
        TYPE S3,
        KEY_ID 'admin',
        SECRET 'admin12345',
        ENDPOINT 'localhost:9000',
        URL_STYLE 'path',
        USE_SSL false
    );
    """)

    con.execute("""
    ATTACH 'host=localhost port=5432 dbname=annapurna_dw user=annapurna password=annapurna123' AS pg (TYPE postgres);
    """)

    query = """
    EXPLAIN ANALYZE
    SELECT 
        st.store_id,
        st.store_name,
        st.city,
        p.category,
        COUNT(s.line_no) AS total_revenue_lines,
        ROUND(SUM(s.qty * s.unit_price), 2) AS category_revenue_inr
    FROM read_parquet('s3://annapurna-lake/year=2024/month=10/store=S01/sales.parquet') s
    JOIN pg.public.stores st ON s.store_id = st.store_id
    JOIN pg.public.products p 
        ON s.product_code = p.product_code 
       AND s.business_date BETWEEN p.valid_from AND p.valid_to
    WHERE s.line_type IN ('SALE', 'RETURN', 'DISCOUNT', 'VOID')
    GROUP BY st.store_id, st.store_name, st.city, p.category
    ORDER BY category_revenue_inr DESC;
    """

    plan = con.execute(query).fetchall()
    print("=== FEDERATED EXPLAIN ANALYZE OUTPUT ===")
    for row in plan:
        print(row[1])

if __name__ == '__main__':
    test_federated()
