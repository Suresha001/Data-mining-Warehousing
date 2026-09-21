import duckdb
import os

def test_historical():
    con = duckdb.connect('annapurna.duckdb')
    con.execute("LOAD postgres;")
    con.execute("ATTACH 'host=localhost port=5432 dbname=annapurna_dw user=annapurna password=annapurna123' AS pg (TYPE postgres);")

    query = """
    WITH reporting_context AS (
        SELECT ?::DATE AS as_of_date
    )
    SELECT 
        dp.product_code,
        dp.product_name,
        dp.category,
        pr.price AS catalog_effective_price,
        pr.effective_from,
        pr.effective_to,
        CAST(COALESCE(SUM(f.quantity), 0) AS BIGINT) AS units_sold_month,
        ROUND(CAST(COALESCE(SUM(f.net_amount), 0) AS DOUBLE), 2) AS realized_net_revenue
    FROM pg.public.price_revisions pr
    JOIN dim_product dp ON pr.product_sk = dp.product_sk
    CROSS JOIN reporting_context rc
    LEFT JOIN fact_sales f 
        ON f.product_sk = dp.product_sk 
       AND strftime(f.date_key, '%Y-%m') = strftime(rc.as_of_date, '%Y-%m')
    WHERE rc.as_of_date BETWEEN pr.effective_from AND pr.effective_to
      AND dp.product_code IN ('P100005', 'P100019', 'P100026', 'P100035', 'P104708')
    GROUP BY dp.product_code, dp.product_name, dp.category, pr.price, pr.effective_from, pr.effective_to
    ORDER BY dp.product_code, dp.product_name;
    """

    print("=" * 110)
    print("RUN 1: PARAMETER = '2024-03-15' (MARCH 2024 HISTORICAL REPORT)")
    print("=" * 110)
    df_mar = con.execute(query, ['2024-03-15']).df()
    print(df_mar.to_string(index=False))

    print("\n" + "=" * 110)
    print("RUN 2: PARAMETER = '2024-10-15' (OCTOBER 2024 HISTORICAL REPORT)")
    print("=" * 110)
    df_oct = con.execute(query, ['2024-10-15']).df()
    print(df_oct.to_string(index=False))

if __name__ == '__main__':
    test_historical()
