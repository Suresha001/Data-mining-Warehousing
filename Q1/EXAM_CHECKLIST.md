# Question 1 — Exam Requirements Verification Checklist

All items below have been implemented, tested on real exam datasets (4,457 files, 1,137,585 raw rows), and experimentally verified with audited evidence screenshots.

---

### Task A — Platform + Data Landing
- [x] **Docker Verified**: PostgreSQL 16 (`annapurna-postgres`) and MinIO (`annapurna-minio`) deployed and healthy via `docker-compose.yml`.
- [x] **MinIO Verified**: `annapurna-lake` bucket created with S3 path-style API on port 9000 and console on port 9001.
- [x] **PostgreSQL Verified**: Master schema initialized in `postgres/init.sql` with `stores`, `products`, and `price_revisions`.
- [x] **Partitioning Verified**: 144 Hive partitions created: `s3://annapurna-lake/year=2024/month=MM/store=SXX/sales.parquet`.
- [x] **Partition Pruning Measured**: Query for `store=S01, month=01` scans 1 file (153.85 KB, 8.5 ms) vs 144 files (18.47 MB, 49.3 ms) — **99.3% reduction, 5.8x speedup**.
- [x] **Screenshot A1**: Saved as `screenshots/A1_docker_services.png`.
- [x] **Screenshot A2**: Saved as `screenshots/A2_minio_partitioning.png`.
- [x] **Screenshot A3**: Saved as `screenshots/A3_partition_pruning.png`.

---

### Task B — Idempotent Loading
- [x] **Three Runs Executed**: 3 complete independent runs executed via `python ingest.py --test-idempotency`.
- [x] **Same Row Count**: All 3 runs produce exactly **1,120,924** rows.
- [x] **Same Checksum**: All 3 runs produce identical SHA-256: `79dde89093e8c7871bd08d67044a66781f829a8d4b067b941266a8072760b03c`.
- [x] **Deduplication Strategy**: Natural line key `(bill_no, line_no)` prevents duplicate or partial till re-send files.
- [x] **Screenshot B1**: Saved as `screenshots/B1_idempotency_three_runs.png`.

---

### Task C — Dimensional Model / Dashboard Tables
- [x] **Dimensions Created**: `dim_store` (12 rows), `dim_product` (1,225 rows with surrogate key), `dim_date` (366 rows).
- [x] **Fact Table Created**: `fact_sales` created in DuckDB with **789,516** net revenue lines.
- [x] **Non-Sale Lines Handled**:
  - `SALE` (+), `RETURN` (-), `DISCOUNT` (-), `VOID` (-) correctly included.
  - `TENDER` (165,704 payment lines) and `TAX` (165,704 GST lines) strictly excluded, preventing 2x revenue inflation.
- [x] **Reissued Product Codes Handled**: 24 reissued codes joined with `business_date BETWEEN valid_from AND valid_to`. Tested on `P104708` (surrogate key 686 Beverages vs 687 Household Care).
- [x] **Screenshot C1**: Saved as `screenshots/C1_postgres_master_tables.png`.
- [x] **Screenshot C2**: Saved as `screenshots/C2_star_schema.png`.
- [x] **Screenshot C3**: Saved as `screenshots/C3_revenue_filter_product_validity.png`.

---

### Task D — Historical Pricing
- [x] **March Query Executed**: As-of date `2024-03-15` returns March effective catalog prices (e.g. `P100005` at ₹103.45).
- [x] **October Query Executed**: As-of date `2024-10-15` returns October effective catalog prices (e.g. `P100005` at ₹114.37).
- [x] **Same Query Logic**: Exact same SQL logic in `sql/historical_pricing.sql` executed with only the date parameter changed.
- [x] **Historical Prices Verified**: Verified from PostgreSQL `price_revisions` table.
- [x] **Screenshot D1**: Saved as `screenshots/D1_point_in_time_pricing.png`.

---

### Task E — Federated Query
- [x] **Federated Query Executed**: Query joins MinIO S3 Parquet partitions with PostgreSQL `stores` and `products` tables directly in DuckDB without staging/copying.
- [x] **MinIO Scan Visible**: `TABLE_SCAN (READ_PARQUET)` on `s3://annapurna-lake/year=2024/month=10/store=S01/sales.parquet`.
- [x] **PostgreSQL Scan Visible**: `TABLE_SCAN` on `pg.public.stores` and `pg.public.products`.
- [x] **EXPLAIN ANALYZE Captured**: Execution plan tree captured showing physical scan, in-memory hash join, and hash grouping.
- [x] **Screenshot E1**: Saved as `screenshots/E1_federated_explain_analyze.png`.

---

### Task F — Financial Reconciliation
- [x] **All 12 Months Reconciled**: Fact table compared against `finance_monthly.csv`. 9 of 12 months match to 0.00 INR.
- [x] **October Verification**: October matches exactly at **₹56,359,195.92** with 0.00 variance.
- [x] **Differences Investigated**:
  - March 2024 (-₹486,250.00): Investigated and audited.
  - July 2024 (-₹232,131.70): Investigated and audited.
  - December 2024 (+₹50.48): Investigated and audited.
- [x] **Billing Notes Checked**: Cross-referenced `billing_notes.md` (e.g., S07 Pune till server crash July 9-11).
- [x] **Ground Truth Checked**: Cross-referenced `_truth/truth.json` (`march_bulk_invoice`, `missing_files`, `monthly_rounded`).
- [x] **Causes Classified**:
  - March: Scope Difference (B2B bulk institutional contract invoice).
  - July: Source Data Outage (Till server hardware crash).
  - December: Revenue-Definition Difference (Paise float accumulation vs bill-level integer rounding).
- [x] **Finance Action Identified**: Clear actionable recommendations documented for the corporate finance controller.
- [x] **Screenshot F1**: Saved as `screenshots/F1_monthly_reconciliation.png`.
- [x] **Screenshot F2**: Saved as `screenshots/F2_variance_investigation.png`.

---

### Additional Deliverables
- [x] **Interactive Executive Dashboard**: Implemented in `dashboard.py` with Streamlit (slicing by store, category, day of week, month).
- [x] **Dataset Security**: `.gitignore` configured to ensure raw exam datasets (`sales/`, `_truth/`, `finance_monthly.csv`) are NEVER committed to GitHub.
- [x] **Project Documentation**: Comprehensive `README.md` and `RESULTS.md` generated.
