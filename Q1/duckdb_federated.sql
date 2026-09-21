-- Task E: DuckDB Federated Analytical Query
-- Joins MinIO Object Storage (Parquet) with PostgreSQL Master Data (stores, products)
-- WITHOUT copying data between systems first.

EXPLAIN ANALYZE
SELECT 
    st.store_id,
    st.store_name,
    st.city,
    p.category,
    COUNT(s.line_no) AS total_revenue_lines,
    ROUND(SUM(s.qty * s.unit_price), 2) AS category_revenue_inr
FROM read_parquet('s3://annapurna-lake/year=2024/month=10/store=S01/sales.parquet') s
JOIN pg.public.stores st 
    ON s.store_id = st.store_id
JOIN pg.public.products p 
    ON s.product_code = p.product_code 
   AND s.business_date BETWEEN p.valid_from AND p.valid_to
WHERE s.line_type IN ('SALE', 'RETURN', 'DISCOUNT', 'VOID')
GROUP BY st.store_id, st.store_name, st.city, p.category
ORDER BY category_revenue_inr DESC;
