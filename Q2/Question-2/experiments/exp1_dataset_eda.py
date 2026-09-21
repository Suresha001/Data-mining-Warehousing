#!/usr/bin/env python3
"""
Question 2: Checkpoint 1 - Dataset Inspection & Profiling
Comprehensive exploratory data analysis on the notices corpus and labelled pairs.
Measures real corpus dimensions, text distributions, portal concentration,
missingness, and pairwise ground-truth properties.
"""

import os
import glob
import json
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Ensure output directories exist
os.makedirs("Question-2/evidence", exist_ok=True)
os.makedirs("Question-2/results", exist_ok=True)

print("=" * 80)
print("  QUESTION 2: CHECKPOINT 1 — DATASET INSPECTION & PROFILING REPORT")
print("=" * 80)

# 1. Load Notices Corpus
notice_files = sorted(glob.glob("notices/part-*.csv"))
print(f"\n[1] NOTICE CORPUS INGESTION")
print(f"    Found {len(notice_files)} partition files: {[os.path.basename(f) for f in notice_files]}")

dfs = [pd.read_csv(f) for f in notice_files]
df_notices = pd.concat(dfs, ignore_index=True)
total_notices = len(df_notices)
unique_notices = df_notices['notice_id'].nunique()
print(f"    Total Notices Ingested : {total_notices:,}")
print(f"    Unique Notice IDs      : {unique_notices:,}")
print(f"    Partitions Uniformity  : {[len(df) for df in dfs]}")

# Missing / Null Statistics
null_counts = df_notices.isnull().sum()
print(f"\n[2] MISSING / NULL VALUE AUDIT ACROSS CORPUS")
for col in df_notices.columns:
    print(f"    - {col:<18} : {null_counts[col]} nulls ({null_counts[col]/total_notices*100:.2f}%)")

# 2. Portal Distribution & Concentration
unique_portals = df_notices['portal_id'].nunique()
portal_counts = df_notices['portal_id'].value_counts()
nodal_portals = ['P001', 'P002', 'P003', 'P004', 'P005', 'P006']
nodal_count = df_notices['portal_id'].isin(nodal_portals).sum()
top_portal = portal_counts.index[0]
top_portal_count = portal_counts.iloc[0]

print(f"\n[3] PORTAL DISTRIBUTION & CONCENTRATION")
print(f"    Total Unique Portals   : {unique_portals}")
print(f"    Top Portal ({top_portal})        : {top_portal_count:,} notices ({top_portal_count/total_notices*100:.2f}%)")
print(f"    Nodal Aggregators P001-6: {nodal_count:,} notices ({nodal_count/total_notices*100:.2f}%)")
print(f"    Top 15 Portals Table   :")
print(f"    {'Rank':<5} {'Portal':<10} {'Notices':<10} {'Percentage':<12} {'Cumul %':<10}")
cum_pct = 0.0
for rank, (p, c) in enumerate(portal_counts.head(15).items(), 1):
    pct = (c / total_notices) * 100
    cum_pct += pct
    print(f"    {rank:<5} {p:<10} {c:<10} {pct:>6.2f}%      {cum_pct:>6.2f}%")

# 3. Text Length Statistics
df_notices['title_char_len'] = df_notices['title'].astype(str).str.len()
df_notices['title_word_len'] = df_notices['title'].astype(str).str.split().apply(len)
df_notices['body_char_len'] = df_notices['body'].astype(str).str.len()
df_notices['body_word_len'] = df_notices['body'].astype(str).str.split().apply(len)

pct_levels = [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
title_char_q = df_notices['title_char_len'].quantile(pct_levels).to_dict()
title_word_q = df_notices['title_word_len'].quantile(pct_levels).to_dict()
body_char_q = df_notices['body_char_len'].quantile(pct_levels).to_dict()
body_word_q = df_notices['body_word_len'].quantile(pct_levels).to_dict()

print(f"\n[4] TEXT LENGTH PERCENTILES (TITLES & BODIES)")
print(f"    {'Metric':<18} {'Min':<6} {'p01':<6} {'p05':<6} {'p25':<7} {'Median':<8} {'Mean':<8} {'p75':<7} {'p95':<7} {'p99':<7} {'Max':<7} {'Std':<7}")
for name, s, q in [
    ("Title Characters", df_notices['title_char_len'], title_char_q),
    ("Title Words", df_notices['title_word_len'], title_word_q),
    ("Body Characters", df_notices['body_char_len'], body_char_q),
    ("Body Words", df_notices['body_word_len'], body_word_q),
]:
    print(f"    {name:<18} {s.min():<6} {q[0.01]:<6.0f} {q[0.05]:<6.0f} {q[0.25]:<7.0f} {s.median():<8.1f} {s.mean():<8.2f} {q[0.75]:<7.0f} {q[0.95]:<7.0f} {q[0.99]:<7.0f} {s.max():<7} {s.std():<7.2f}")

# 4. Monetary Value & Closing Date Audit
unique_values = df_notices['estimated_value'].nunique()
val_min = df_notices['estimated_value'].min()
val_med = df_notices['estimated_value'].median()
val_max = df_notices['estimated_value'].max()
print(f"\n[5] ATTRIBUTE VALUE PROFILING")
print(f"    Unique estimated_values: {unique_values:,} (avg {total_notices/unique_values:.2f} notices/value)")
print(f"    estimated_value Range  : Min = Rs {val_min:,} | Median = Rs {val_med:,.0f} | Max = Rs {val_max:,}")
print(f"    Notices with Value == 0: {(df_notices['estimated_value'] == 0).sum()}")

# 5. Load Labelled Pairs (Ground Truth)
df_labels = pd.read_csv("labelled_pairs.csv")
total_pairs = len(df_labels)
label_counts = df_labels['label'].value_counts()
n_diff = label_counts.get('different', 0)
n_same = label_counts.get('same', 0)
pct_diff = (n_diff / total_pairs) * 100
pct_same = (n_same / total_pairs) * 100
imbalance_ratio = n_diff / n_same if n_same > 0 else 0

pair_notices = set(df_labels['notice_id_a']).union(set(df_labels['notice_id_b']))
all_in_corpus = pair_notices.issubset(set(df_notices['notice_id']))

print(f"\n[6] LABELLED PAIRS GROUND-TRUTH AUDIT (labelled_pairs.csv)")
print(f"    Total Adjudicated Pairs: {total_pairs}")
print(f"    - DIFFERENT Pairs      : {n_diff} ({pct_diff:.2f}%)")
print(f"    - SAME Pairs           : {n_same} ({pct_same:.2f}%)")
print(f"    - Imbalance Ratio      : {imbalance_ratio:.2f} : 1 (Different : Same)")
print(f"    - Unique Notices in Set: {len(pair_notices)}")
print(f"    - All Pair IDs in Corpus: {all_in_corpus}")

# 6. Pairwise Attribute Agreement Analysis
notices_idx = df_notices.set_index('notice_id')
same_df = df_labels[df_labels['label'] == 'same']
diff_df = df_labels[df_labels['label'] == 'different']

def get_pair_agreements(subset):
    same_val = sum(notices_idx.loc[r.notice_id_a, 'estimated_value'] == notices_idx.loc[r.notice_id_b, 'estimated_value'] for _, r in subset.iterrows())
    same_close = sum(notices_idx.loc[r.notice_id_a, 'closing_date'] == notices_idx.loc[r.notice_id_b, 'closing_date'] for _, r in subset.iterrows())
    same_portal = sum(notices_idx.loc[r.notice_id_a, 'portal_id'] == notices_idx.loc[r.notice_id_b, 'portal_id'] for _, r in subset.iterrows())
    return same_val, same_close, same_portal

same_val_s, same_close_s, same_portal_s = get_pair_agreements(same_df)
same_val_d, same_close_d, same_portal_d = get_pair_agreements(diff_df)

print(f"\n[7] PAIRWISE ATTRIBUTE AGREEMENT MATRIX")
print(f"    {'Attribute':<20} {'SAME Pairs (N=279)':<25} {'DIFFERENT Pairs (N=621)':<25}")
print(f"    {'-'*20} {'-'*25} {'-'*25}")
print(f"    {'estimated_value match':<20} {same_val_s}/{n_same} ({same_val_s/n_same*100:>6.2f}%)          {same_val_d}/{n_diff} ({same_val_d/n_diff*100:>6.2f}%)")
print(f"    {'closing_date match':<20} {same_close_s}/{n_same} ({same_close_s/n_same*100:>6.2f}%)          {same_close_d}/{n_diff} ({same_close_d/n_diff*100:>6.2f}%)")
print(f"    {'portal_id match':<20} {same_portal_s}/{n_same} ({same_portal_s/n_same*100:>6.2f}%)          {same_portal_d}/{n_diff} ({same_portal_d/n_diff*100:>6.2f}%)")

# 7. Common Preamble Boilerplate Verification
print(f"\n[8] NODAL BOILERPLATE PREAMBLE VERIFICATION")
for pid in ['P001', 'P002', 'P003', 'P004', 'P005', 'P006', 'P094']:
    sub = df_notices[df_notices['portal_id'] == pid]
    b1 = sub.iloc[0]['body']
    b2 = sub.iloc[1]['body']
    cp = 0
    while cp < min(len(b1), len(b2)) and b1[cp] == b2[cp]:
        cp += 1
    sample_text = b1[:60].replace('\n', ' ')
    print(f"    Portal {pid:<6}: Count={len(sub):<5} | Identical Prefix Length={cp:<5} chars | Sample: '{sample_text}...'")

# Save Metrics JSON
metrics = {
    "corpus": {
        "total_notices": total_notices,
        "unique_portals": unique_portals,
        "partitions_count": len(notice_files),
        "zero_nulls": bool(null_counts.sum() == 0),
        "top_portal": {"portal_id": top_portal, "count": int(top_portal_count), "pct": float(top_portal_count/total_notices*100)},
        "nodal_portals_count": int(nodal_count),
        "nodal_portals_pct": float(nodal_count/total_notices*100)
    },
    "text_lengths": {
        "title_chars": {"min": int(df_notices['title_char_len'].min()), "median": float(df_notices['title_char_len'].median()), "mean": float(df_notices['title_char_len'].mean()), "max": int(df_notices['title_char_len'].max())},
        "body_chars": {"min": int(df_notices['body_char_len'].min()), "median": float(df_notices['body_char_len'].median()), "mean": float(df_notices['body_char_len'].mean()), "max": int(df_notices['body_char_len'].max())}
    },
    "labelled_pairs": {
        "total": total_pairs,
        "different": int(n_diff),
        "same": int(n_same),
        "diff_pct": float(pct_diff),
        "same_pct": float(pct_same),
        "imbalance_ratio": float(imbalance_ratio)
    },
    "pairwise_agreement": {
        "same_pairs": {"estimated_value_pct": float(same_val_s/n_same*100), "closing_date_pct": float(same_close_s/n_same*100), "same_portal_pct": float(same_portal_s/n_same*100)},
        "diff_pairs": {"estimated_value_pct": float(same_val_d/n_diff*100), "closing_date_pct": float(same_close_d/n_diff*100), "same_portal_pct": float(same_portal_d/n_diff*100)}
    }
}

with open("Question-2/results/eda_metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)
print(f"\n[OK] Machine-readable metrics saved to Question-2/results/eda_metrics.json")

# 8. Generate Visual Evidence Chart (eda_dataset_profile.png)
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Question 2 - Checkpoint 1: Dataset Inspection & Profiling", fontsize=16, fontweight='bold')

# Subplot 1: Label Imbalance
ax1 = axes[0, 0]
colors = ['#e74c3c', '#2ecc71']
bars = ax1.bar(['DIFFERENT (621)', 'SAME (279)'], [n_diff, n_same], color=colors, edgecolor='black', width=0.5)
ax1.set_title("Labelled Pairs Ground Truth (N=900)", fontsize=12, fontweight='bold')
ax1.set_ylabel("Pair Count")
ax1.set_ylim(0, 750)
for bar, pct in zip(bars, [pct_diff, pct_same]):
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 15, f"{yval} ({pct:.1f}%)\nRatio: {imbalance_ratio:.2f}:1", ha='center', va='bottom', fontweight='bold')

# Subplot 2: Top Portals
ax2 = axes[0, 1]
top10 = portal_counts.head(10)
bars2 = ax2.bar(top10.index, top10.values, color='#3498db', edgecolor='black')
# Highlight nodal portals in orange
for idx, p in enumerate(top10.index):
    if p in nodal_portals:
        bars2[idx].set_color('#e67e22')
ax2.set_title("Top 10 Portals (Orange = Nodal Aggregators P001-P006)", fontsize=12, fontweight='bold')
ax2.set_ylabel("Notice Count")
ax2.tick_params(axis='x', rotation=45)
for bar in bars2:
    yval = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 15, f"{yval}", ha='center', va='bottom', fontsize=9)

# Subplot 3: Body Length Distribution
ax3 = axes[1, 0]
ax3.hist(df_notices['body_char_len'], bins=40, color='#9b59b6', edgecolor='black', alpha=0.8)
ax3.axvline(df_notices['body_char_len'].median(), color='red', linestyle='--', linewidth=2, label=f"Median: {df_notices['body_char_len'].median():,.0f} chars")
ax3.axvline(df_notices['body_char_len'].mean(), color='blue', linestyle=':', linewidth=2, label=f"Mean: {df_notices['body_char_len'].mean():,.0f} chars")
ax3.set_title("Corpus Body Length Distribution (Chars)", fontsize=12, fontweight='bold')
ax3.set_xlabel("Body Character Length")
ax3.set_ylabel("Frequency")
ax3.legend()

# Subplot 4: Pairwise Attribute Agreement
ax4 = axes[1, 1]
attrs = ['estimated_value', 'closing_date', 'portal_id']
same_vals_pct = [same_val_s/n_same*100, same_close_s/n_same*100, same_portal_s/n_same*100]
diff_vals_pct = [same_val_d/n_diff*100, same_close_d/n_diff*100, same_portal_d/n_diff*100]
x = np.arange(len(attrs))
width = 0.35
ax4.bar(x - width/2, same_vals_pct, width, label='SAME Pairs', color='#2ecc71', edgecolor='black')
ax4.bar(x + width/2, diff_vals_pct, width, label='DIFFERENT Pairs', color='#e74c3c', edgecolor='black')
ax4.set_title("Attribute Agreement: SAME vs DIFFERENT Pairs", fontsize=12, fontweight='bold')
ax4.set_ylabel("Agreement Percentage (%)")
ax4.set_xticks(x)
ax4.set_xticklabels(['Estimated Value', 'Closing Date', 'Portal ID'])
ax4.set_ylim(0, 115)
ax4.legend()
for i in range(len(attrs)):
    ax4.text(x[i] - width/2, same_vals_pct[i] + 2, f"{same_vals_pct[i]:.1f}%", ha='center', fontsize=9, fontweight='bold')
    ax4.text(x[i] + width/2, diff_vals_pct[i] + 2, f"{diff_vals_pct[i]:.1f}%", ha='center', fontsize=9, fontweight='bold')

plt.tight_layout()
evidence_path = "Question-2/evidence/eda_dataset_profile.png"
plt.savefig(evidence_path, dpi=150)
plt.close()
print(f"[OK] Visual evidence chart generated and saved to {evidence_path}")
print("=" * 80)
print("  CHECKPOINT 1 COMPLETED SUCCESSFULLY")
print("=" * 80)
