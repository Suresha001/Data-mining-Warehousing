import streamlit as st
import duckdb
import pandas as pd

st.set_page_config(page_title="Annapurna Store - Modern Data Lakehouse Dashboard", layout="wide")

st.title("🛒 Annapurna Store Modern Data Lakehouse Dashboard")
st.markdown("### Executive Sales Analytics & Dimensional Slicing (Question 1)")

@st.cache_resource
def get_connection():
    return duckdb.connect('annapurna.duckdb', read_only=True)

con = get_connection()

# Sidebar Filters
st.sidebar.header("Navigation & Dimensional Filters")

# Stores
stores_df = con.execute("SELECT store_id, store_name, city FROM dim_store ORDER BY store_id").df()
store_options = ["All Stores"] + [f"{r['store_id']} - {r['store_name']} ({r['city']})" for _, r in stores_df.iterrows()]
selected_store = st.sidebar.selectbox("Select Store", store_options)

# Categories
cats_df = con.execute("SELECT DISTINCT category FROM dim_product WHERE category != 'N/A' ORDER BY category").df()
cat_options = ["All Categories"] + cats_df['category'].tolist()
selected_category = st.sidebar.selectbox("Select Product Category", cat_options)

# Months
months = [
    "All Months", "2024-01", "2024-02", "2024-03", "2024-04", 
    "2024-05", "2024-06", "2024-07", "2024-08", "2024-09", 
    "2024-10", "2024-11", "2024-12"
]
selected_month = st.sidebar.selectbox("Select Month", months)

# Days of Week
dow_options = ["All Days", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
selected_dow = st.sidebar.selectbox("Select Day of Week", dow_options)

# Build Dynamic Filter Query
where_clauses = ["1=1"]
params = []

if selected_store != "All Stores":
    s_id = selected_store.split(" - ")[0]
    where_clauses.append("f.store_id = ?")
    params.append(s_id)

if selected_category != "All Categories":
    where_clauses.append("p.category = ?")
    params.append(selected_category)

if selected_month != "All Months":
    where_clauses.append("d.month_str = ?")
    params.append(selected_month)

if selected_dow != "All Days":
    where_clauses.append("d.day_name = ?")
    params.append(selected_dow)

where_sql = " AND ".join(where_clauses)

# KPI Summary Cards
kpi_query = f"""
SELECT 
    COUNT(*) AS total_transactions,
    ROUND(SUM(f.net_amount), 2) AS total_net_revenue,
    ROUND(AVG(f.net_amount), 2) AS avg_item_revenue,
    SUM(f.quantity) AS total_quantity
FROM fact_sales f
JOIN dim_store s ON f.store_id = s.store_id
JOIN dim_product p ON f.product_sk = p.product_sk
JOIN dim_date d ON CAST(f.date_key AS DATE) = d.date_key
WHERE {where_sql}
"""
kpi_df = con.execute(kpi_query, params).df()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Net Revenue (INR)", f"₹{kpi_df['total_net_revenue'].iloc[0]:,.2f}" if pd.notnull(kpi_df['total_net_revenue'].iloc[0]) else "₹0.00")
with col2:
    st.metric("Total Transaction Lines", f"{kpi_df['total_transactions'].iloc[0]:,}")
with col3:
    st.metric("Units Sold", f"{int(kpi_df['total_quantity'].iloc[0]):,}" if pd.notnull(kpi_df['total_quantity'].iloc[0]) else "0")
with col4:
    st.metric("Avg Item Revenue (INR)", f"₹{kpi_df['avg_item_revenue'].iloc[0]:,.2f}" if pd.notnull(kpi_df['avg_item_revenue'].iloc[0]) else "₹0.00")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Slicing Breakdown", "📈 Monthly Trend", "🏷️ Top Categories & Products"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Revenue by Store")
        store_q = f"""
        SELECT s.store_id, s.store_name, ROUND(SUM(f.net_amount), 2) AS net_revenue
        FROM fact_sales f
        JOIN dim_store s ON f.store_id = s.store_id
        JOIN dim_product p ON f.product_sk = p.product_sk
        JOIN dim_date d ON CAST(f.date_key AS DATE) = d.date_key
        WHERE {where_sql}
        GROUP BY s.store_id, s.store_name
        ORDER BY net_revenue DESC
        """
        st.dataframe(con.execute(store_q, params).df(), use_container_width=True)

    with c2:
        st.subheader("Revenue by Day of Week")
        dow_q = f"""
        SELECT d.day_name, ROUND(SUM(f.net_amount), 2) AS net_revenue
        FROM fact_sales f
        JOIN dim_store s ON f.store_id = s.store_id
        JOIN dim_product p ON f.product_sk = p.product_sk
        JOIN dim_date d ON CAST(f.date_key AS DATE) = d.date_key
        WHERE {where_sql}
        GROUP BY d.day_name, d.day_of_week
        ORDER BY d.day_of_week
        """
        st.dataframe(con.execute(dow_q, params).df(), use_container_width=True)

with tab2:
    st.subheader("Monthly Net Revenue Trend (2024)")
    trend_q = f"""
    SELECT d.month_str, ROUND(SUM(f.net_amount), 2) AS net_revenue
    FROM fact_sales f
    JOIN dim_store s ON f.store_id = s.store_id
    JOIN dim_product p ON f.product_sk = p.product_sk
    JOIN dim_date d ON CAST(f.date_key AS DATE) = d.date_key
    WHERE {where_sql}
    GROUP BY d.month_str
    ORDER BY d.month_str
    """
    trend_df = con.execute(trend_q, params).df()
    st.line_chart(trend_df.set_index('month_str'))

with tab3:
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Revenue by Product Category")
        cat_q = f"""
        SELECT p.category, ROUND(SUM(f.net_amount), 2) AS net_revenue
        FROM fact_sales f
        JOIN dim_store s ON f.store_id = s.store_id
        JOIN dim_product p ON f.product_sk = p.product_sk
        JOIN dim_date d ON CAST(f.date_key AS DATE) = d.date_key
        WHERE {where_sql}
        GROUP BY p.category
        ORDER BY net_revenue DESC
        """
        st.dataframe(con.execute(cat_q, params).df(), use_container_width=True)

    with c4:
        st.subheader("Top 10 Selling Products")
        prod_q = f"""
        SELECT p.product_code, p.product_name, p.category, ROUND(SUM(f.net_amount), 2) AS net_revenue
        FROM fact_sales f
        JOIN dim_store s ON f.store_id = s.store_id
        JOIN dim_product p ON f.product_sk = p.product_sk
        JOIN dim_date d ON CAST(f.date_key AS DATE) = d.date_key
        WHERE {where_sql}
        GROUP BY p.product_code, p.product_name, p.category
        ORDER BY net_revenue DESC
        LIMIT 10
        """
        st.dataframe(con.execute(prod_q, params).df(), use_container_width=True)
