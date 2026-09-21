import matplotlib.pyplot as plt
import numpy as np

# Data from verified F1 / F2 results
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
finance_rev = np.array([38446071.33, 34887085.55, 42457899.09, 37958457.37, 41764716.40, 38987082.82,
                        40527291.81, 45252181.75, 44615037.46, 56359195.92, 51583838.47, 50745209.00]) / 1e6
pipeline_rev = np.array([38446071.33, 34887085.55, 41971649.09, 37958457.37, 41764716.40, 38987082.82,
                         40295160.11, 45252181.75, 44615037.46, 56359195.92, 51583838.47, 50745259.48]) / 1e6

variance_inr = np.array([0.00, 0.00, -486250.00, 0.00, 0.00, 0.00, -232131.70, 0.00, 0.00, 0.00, 0.00, 50.48])

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 8.5), dpi=300, gridspec_kw={'height_ratios': [2, 1.2]})

x = np.arange(len(months))
width = 0.38

# Panel 1: Revenue Comparison
rects1 = ax1.bar(x - width/2, finance_rev, width, label='Finance Target Revenue (finance_monthly.csv)', 
                 color='#0284c7', edgecolor='#0369a1', linewidth=1)
rects2 = ax1.bar(x + width/2, pipeline_rev, width, label='Lakehouse Pipeline Revenue (fact_sales)', 
                 color='#10b981', edgecolor='#047857', linewidth=1)

ax1.set_title('Annapurna Lakehouse — Monthly Net Revenue Comparison: Finance Target vs Pipeline (2024)', 
              fontsize=14, fontweight='bold', pad=12, color='#0f172a')
ax1.set_ylabel('Net Revenue (Million INR)', fontsize=11, fontweight='semibold', color='#334155')
ax1.set_xticks(x)
ax1.set_xticklabels(months, fontsize=11, fontweight='semibold')
ax1.set_ylim(25, 65)
ax1.legend(loc='upper left', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1', fontsize=10.5)
ax1.grid(axis='y', linestyle='--', alpha=0.5)

# Highlight October
ax1.annotate('October CFO Sign-off: ₹56.36M\nExact Match (Zero 2x Inflation)',
             xy=(9, 56.36), xytext=(8.5, 61.5),
             arrowprops=dict(arrowstyle='->', lw=1.5, color='#b91c1c'),
             ha='center', fontsize=9.5, fontweight='bold', color='#991b1b',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#fee2e2', edgecolor='#fca5a5'))

# Panel 2: Monthly Variance Breakdown
var_k = variance_inr / 1e3
colors = ['#16a34a' if v == 0 else ('#dc2626' if v < 0 else '#f59e0b') for v in variance_inr]
bars = ax2.bar(x, var_k, width=0.5, color=colors, edgecolor='#333333', linewidth=1)

ax2.axhline(0, color='#64748b', linewidth=1.2)
ax2.set_title('Monthly Revenue Variance (Pipeline Revenue − Finance Revenue in Thousand INR)', 
              fontsize=13, fontweight='bold', pad=10, color='#0f172a')
ax2.set_ylabel('Variance (Thousand INR)', fontsize=10.5, fontweight='semibold', color='#334155')
ax2.set_xticks(x)
ax2.set_xticklabels(months, fontsize=11, fontweight='semibold')
ax2.set_ylim(-600, 200)
ax2.grid(axis='y', linestyle='--', alpha=0.5)

# Annotate variances
ax2.annotate('March: -₹486.25K\n(B2B Bulk Invoice outside till)',
             xy=(2, -486.25), xytext=(2, -220),
             arrowprops=dict(arrowstyle='->', lw=1.2, color='#b91c1c'),
             ha='center', fontsize=9, fontweight='bold', color='#7f1d1d',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#fef2f2', edgecolor='#fecaca'))

ax2.annotate('July: -₹232.13K\n(S07 Pune server outage 3 days)',
             xy=(6, -232.13), xytext=(6, 50),
             arrowprops=dict(arrowstyle='->', lw=1.2, color='#b91c1c'),
             ha='center', fontsize=9, fontweight='bold', color='#7f1d1d',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#fef2f2', edgecolor='#fecaca'))

ax2.annotate('Dec: +₹0.05K\n(+₹50.48 Paise vs Rupee Rounding)',
             xy=(11, 0.05), xytext=(10.5, 90),
             arrowprops=dict(arrowstyle='->', lw=1.2, color='#d97706'),
             ha='center', fontsize=9, fontweight='bold', color='#78350f',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffbeb', edgecolor='#fef3c7'))

# 9 Exact match callout
ax2.text(0.5, 0.85, '9 of 12 Months: 100% Exact Match (0.00 INR Variance)', transform=ax2.transAxes,
         ha='center', va='center', fontsize=10.5, fontweight='bold', color='#15803d',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#dcfce7', edgecolor='#86efac', lw=1.2))

plt.tight_layout()
plt.savefig('screenshots/financial_reconciliation_chart.png', bbox_inches='tight')
print("Saved screenshots/financial_reconciliation_chart.png successfully!")
