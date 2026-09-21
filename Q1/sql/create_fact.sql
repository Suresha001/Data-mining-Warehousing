-- SQL Star Schema Creation Script
-- Annapurna Store Modern Lakehouse

-- 1. dim_store
CREATE OR REPLACE TABLE dim_store AS
SELECT 
    store_id,
    store_name,
    city,
    state
FROM pg.public.stores;

-- 2. dim_product (SCD-2 with 1224 rows handling reissued product codes + special discount surrogate)
CREATE OR REPLACE TABLE dim_product AS
SELECT 
    product_sk,
    product_code,
    product_name,
    category,
    valid_from,
    valid_to
FROM pg.public.products;

INSERT INTO dim_product (product_sk, product_code, product_name, category, valid_from, valid_to)
VALUES (0, 'DISCOUNT', 'Bill-Level Discount', 'Promotions & Discounts', '2024-01-01', '2099-12-31');

-- 3. dim_date (2024 Calendar Year with Day-of-Week and Month dimensions)
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

-- 4. fact_sales (Filtered for revenue lines: excludes TAX & TENDER)
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
