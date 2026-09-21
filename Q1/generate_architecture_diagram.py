import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.axis('off')

# Background canvas
fig.patch.set_facecolor('#f8fafc')
ax.set_facecolor('#f8fafc')

def draw_box(ax, x, y, w, h, title, subtitle, items, box_color, border_color, title_color='#0f172a'):
    # Card shadow
    shadow = patches.FancyBboxPatch((x + 0.06, y - 0.06), w, h,
                                    boxstyle="round,pad=0.1,rounding_size=0.2",
                                    facecolor='#e2e8f0', edgecolor='none', zorder=1)
    ax.add_patch(shadow)
    
    # Card body
    card = patches.FancyBboxPatch((x, y), w, h,
                                  boxstyle="round,pad=0.1,rounding_size=0.2",
                                  facecolor=box_color, edgecolor=border_color, linewidth=1.8, zorder=2)
    ax.add_patch(card)
    
    # Header bar
    ax.text(x + w/2, y + h - 0.35, title, ha='center', va='center', fontsize=11.5, fontweight='bold', color=title_color, zorder=3)
    if subtitle:
        ax.text(x + w/2, y + h - 0.65, subtitle, ha='center', va='center', fontsize=8.5, fontweight='semibold', color='#64748b', zorder=3)
    
    # Dividing line
    ax.plot([x + 0.2, x + w - 0.2], [y + h - 0.85, y + h - 0.85], color=border_color, linewidth=1, alpha=0.6, zorder=3)
    
    # Content items
    item_y = y + h - 1.2
    for item in items:
        ax.text(x + 0.3, item_y, f"• {item}", ha='left', va='center', fontsize=8.8, color='#334155', zorder=3)
        item_y -= 0.38

def draw_arrow(ax, x1, y1, x2, y2, label=None, label_pos=(0, 0)):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color='#2563eb', lw=2, mutation_scale=15),
                zorder=4)
    if label:
        lx = (x1 + x2) / 2 + label_pos[0]
        ly = (y1 + y2) / 2 + label_pos[1]
        ax.text(lx, ly, label, ha='center', va='center', fontsize=8, fontweight='bold',
                color='#1e40af', bbox=dict(boxstyle='round,pad=0.2', facecolor='#dbeafe', edgecolor='#93c5fd', lw=1),
                zorder=5)

# Title Header
ax.text(8, 8.5, "Annapurna Store — Modern Data Lakehouse Architecture", 
        ha='center', va='center', fontsize=17, fontweight='bold', color='#0f172a')
ax.text(8, 8.1, "MinIO Object Storage + PostgreSQL Operational DB + DuckDB In-Memory Analytical Engine", 
        ha='center', va='center', fontsize=10.5, fontweight='semibold', color='#475569')

# Column 1: Sources & Ingestion
draw_box(ax, 0.6, 4.3, 3.2, 3.2, 
         "1. POS Till Exports", "4,457 Files (12 Stores)", 
         ["Stores S01-S05: Comma, ISO-8601",
          "Stores S06-S09: Semicolon, DD-MM-YY",
          "Stores S10-S12: BOM, Epoch Sec",
          "Includes Returns, Discounts, Voids",
          "Raw Lines: 1,137,585"],
         '#ffffff', '#cbd5e1')

draw_box(ax, 0.6, 0.6, 3.2, 3.2, 
         "2. Python Ingestion", "ingest.py Engine", 
         ["Dialect Normalization Parser",
          "Line Key: (bill_no, line_no)",
          "Deduplicated: 1,120,924 Rows",
          "Deterministic Idempotency",
          "SHA-256 Checksum Verified"],
         '#ffffff', '#cbd5e1')

# Column 2: Storage Layers
draw_box(ax, 4.5, 4.3, 3.4, 3.2, 
         "3. MinIO Object Store", "Data Lake: annapurna-lake", 
         ["144 Hive Partitions (.parquet)",
          "Path: year=2024/month=MM/store=SXX",
          "Snappy Columnar Compression",
          "Task A3 Pruning: 99.3% Reduction",
          "1 File (153 KB) vs 144 Files (18 MB)"],
         '#eff6ff', '#93c5fd', '#1e40af')

draw_box(ax, 4.5, 0.6, 3.4, 3.2, 
         "4. PostgreSQL 16", "Operational DB: annapurna_dw", 
         ["stores (12 Supermarkets)",
          "products (1,224 Master Rows)",
          "SCD-2 Handling for 24 Reissued Codes",
          "price_revisions (2,876 Rows)",
          "Effective-Dated Pricing History"],
         '#eff6ff', '#93c5fd', '#1e40af')

# Column 3: DuckDB Engine & Star Schema
draw_box(ax, 8.6, 4.3, 3.4, 3.2, 
         "5. DuckDB Engine", "Vectorized Analytical Core", 
         ["httpfs Extension (S3 API Client)",
          "postgres Extension (Direct Attach)",
          "Zero-Copy Query Federation",
          "Filter: line_type IN (Revenue)",
          "October 2x Tax/Tender Safeguard"],
         '#fefce8', '#fde047', '#854d0e')

draw_box(ax, 8.6, 0.6, 3.4, 3.2, 
         "6. Star Schema", "annapurna.duckdb Warehouse", 
         ["dim_store (12 Rows)",
          "dim_product (1,225 Rows)",
          "dim_date (366 Days - Leap 2024)",
          "fact_sales (789,516 Rows)",
          "Annual Net Rev: ₹522,865,735.75"],
         '#fefce8', '#fde047', '#854d0e')

# Column 4: Analytics & Reconciliation
draw_box(ax, 12.7, 4.3, 2.7, 3.2, 
         "7. Streamlit BI", "dashboard.py", 
         ["Multi-Dimensional Slicing",
          "By Store & City",
          "By Product Category",
          "By Day of Week",
          "By Monthly Trend"],
         '#f0fdf4', '#86efac', '#166534')

draw_box(ax, 12.7, 0.6, 2.7, 3.2, 
         "8. Reconciliation", "reconcile.py Engine", 
         ["Audits vs finance_monthly.csv",
          "9 Months Exact Match (0.00 Diff)",
          "March: -₹486K B2B Bulk Order",
          "July: -₹232K S07 Pune Outage",
          "Dec: +₹50 Paise Rounding"],
         '#f0fdf4', '#86efac', '#166534')

# Arrows
draw_arrow(ax, 2.2, 4.3, 2.2, 3.9)
draw_arrow(ax, 3.9, 2.2, 4.5, 5.5, "Upload Parquet", (0, 0.2))
draw_arrow(ax, 7.9, 5.9, 8.6, 5.9, "s3:// read", (0, 0.25))
draw_arrow(ax, 7.9, 2.2, 8.6, 2.2, "Attach PG", (0, 0.25))
draw_arrow(ax, 10.3, 4.3, 10.3, 3.9, "Build Model")
draw_arrow(ax, 12.0, 5.9, 12.7, 5.9, "Query")
draw_arrow(ax, 12.0, 2.2, 12.7, 2.2, "Audit")

plt.tight_layout()
plt.savefig('screenshots/architecture_diagram.png', bbox_inches='tight')
print("Saved screenshots/architecture_diagram.png successfully!")
