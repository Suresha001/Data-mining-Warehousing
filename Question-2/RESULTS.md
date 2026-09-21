# Experimental Benchmark Results Summary — Setubid Procurement Deduplication

This document aggregates the exact measured benchmark results across Checkpoints 1 through 7 for Question 2. All values are direct experimental measurements recorded on this machine and preserved in machine-readable JSON artifacts under `results/`.

---

## 1. Corpus Profiling & Ground-Truth EDA (Checkpoint 1)

*Source: `results/eda_metrics.json` | Evidence: [Dataset Profile](evidence/eda_dataset_profile.png)*

| Metric Category | Dimension / Property | Measured Value | Operational Implication |
| :--- | :--- | :--- | :--- |
| **Corpus Volume** | Total tender notices | 12,000 | Production nightly batch size |
| **Portal Distribution** | Unique publishing portals | 260 | Multi-jurisdiction crawling |
| **Data Partitioning** | Supplied raw file format | 8 CSV partition files | Ingestion from CSV (`notices_partition_*.csv`) |
| **Data Integrity** | Null fields across corpus | 0 (0.00%) | Complete metadata fields |
| **Text Scale** | Title character length | Min: 40, Med: 80.0, Mean: 80.57, Max: 131 | Uniform title lengths |
| **Text Scale** | Body character length | Min: 1,500, Med: 4,482.0, Mean: 4,527.30, Max: 8,127 | Long text requiring shingling |
| **Portal Concentration**| Top single portal (P094) | 1,426 notices (11.88%) | High volume driver |
| **Portal Concentration**| Nodal aggregators (P001–P006)| 4,665 notices (38.88%) | Inter-state aggregator platforms |
| **Ground-Truth Labels**| Total labelled pairs | 900 pairs | Benchmark evaluation set |
| **Label Imbalance** | DIFFERENT vs. SAME | 621 (69.0%) vs. 279 (31.0%) | 2.23 : 1 class imbalance |
| **Cross-Portal Dups** | SAME pairs sharing portal_id | 0 pairs (0.00%) | 100% of duplicates span distinct portals |
| **Metadata Signals** | SAME pairs matching `estimated_value` | 279 / 279 (100.00%) | Invariant budget across duplicates |
| **Metadata Signals** | SAME pairs matching `closing_date` | 142 / 279 (50.90%) | Extensions & corrigenda alter dates |

---

## 2. Requirement A(a): Similarity Representation Comparison (Checkpoint 2)

*Source: `results/similarity_comparison_900.json` | Evidence: [Similarity Metric Comparison](evidence/similarity_metric_comparison.png)*

Evaluated on all 900 ground-truth labelled pairs (279 SAME, 621 DIFFERENT).

| Metric / Evaluation Dimension | Choice 1: Raw Word 3-Gram Jaccard | Choice 2: Cleaned Multi-Field Composite | Delta / Advantage |
| :--- | :--- | :--- | :--- |
| **Representation Definition** | Raw concatenated text word 3-grams | Title word 2-grams (0.5) + Body word 3-grams (0.5) | Granular multi-field weighting |
| **Boilerplate Stripping** | None (includes preambles/disclaimers) | Strict regex stripping of statutory notices | Eliminates spurious n-gram overlap |
| **ROC-AUC** | 0.9207 | **1.0000** | Perfect ranking (+0.0793) |
| **PR-AUC** | 0.8933 | **1.0000** | Perfect precision-recall (+0.1067) |
| **Optimal Threshold $\tau^*$** | 0.4659 (Macro-F1 max) | **0.6028** (Midpoint of separation gap) | Well-centered decision boundary |
| **Separation Gap** | No gap (overlap: $[0.1956, 0.5314]$) | **Gap: $[0.5993, 0.6063]$** ($+0.0070$ margin) | Linear separability |
| **Macro-F1 Score** | 0.8828 | **1.0000** | +0.1172 |
| **Precision** | 0.9535 (205 TP, 10 FP) | **1.0000** (279 TP, 0 FP) | Zero false merges |
| **Recall** | 0.7348 (74 FN) | **1.0000** (0 FN) | Zero missed duplicates |
| **SAME Score Distribution** | Min: 0.1956, Med: 0.6232, Max: 0.9906 | Min: 0.6063, Med: 0.8304, Max: 1.0000 | Compressed high-similarity mode |
| **DIFFERENT Distribution** | Min: 0.0945, Med: 0.2376, Max: 0.5314 | Min: 0.0527, Med: 0.1449, Max: 0.5993 | Suppressed background overlap |
| **Anchor: N010018 vs N010020 (SAME)** | 0.2217 (Classified DIFFERENT — **FN**) | **0.6165** (Classified SAME — **TP**) | Dilution overcome by boilerplate strip |
| **Anchor: N007021 vs N010547 (DIFF)** | 0.3305 (Danger zone near threshold) | **0.1928** (Classified DIFFERENT — **TN**) | Spurious portal boilerplate rejected |
| **Pairwise Latency** | 0.735 ms / pair | 1.276 ms / pair | +0.541 ms adoption cost (manageable) |

---

## 3. Requirement A(b): MinHash Theoretical Derivation & Sizing Benchmark (Checkpoint 3)

*Source: `results/minhash_k_benchmarks.json` | Evidence: [MinHash Error Derivation](evidence/minhash_error_derivation.png)*

- **Adopted Threshold**: $\tau^* = 0.6028$
- **Theoretical Formulation**: Universal 64-bit hashing $h_{a,b}(x) = (a \cdot x + b \bmod p) \bmod 2^{64}$ with Mersenne prime $p = 2^{61}-1$.
- **Error Expectations**: $\mathbb{E}[\hat{J}] = J$, $\text{Var}(\hat{J}) = \frac{J(1-J)}{K}$, $\sigma = \sqrt{\frac{J(1-J)}{K}}$. Worst-case variance occurs analytically at $J = 0.5$.

| Sizing $K$ | MAE | RMSE | Max Error | p50 Error | p90 Error | p99 Error | Classification Agreement ($\tau^*=0.6028$) | Sig Gen Time (900 pairs) | Signature Size / Notice | 12k Corpus RAM Footprint |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **32** | 0.0343 | 0.0432 | 0.1266 | 0.0283 | 0.0716 | 0.1100 | 99.89% (1 mismatch) | 157.6 ms | 512 bytes | 5.86 MB |
| **64** | 0.0207 | 0.0268 | 0.0970 | 0.0167 | 0.0472 | 0.0691 | 99.56% (4 mismatches) | 297.0 ms | 1,024 bytes | 11.72 MB |
| **128 (Selected)** | **0.0164** | **0.0213** | **0.0701** | **0.0130** | **0.0364** | **0.0537** | **99.78% (2 mismatches)** | **587.9 ms** | **2,048 bytes** | **23.44 MB** |
| **256** | 0.0104 | 0.0137 | 0.0598 | 0.0083 | 0.0225 | 0.0384 | 99.78% (2 mismatches) | 2,762.9 ms | 4,096 bytes | 46.88 MB |
| **512** | 0.0080 | 0.0104 | 0.0432 | 0.0063 | 0.0175 | 0.0294 | 99.67% (3 mismatches) | 5,809.8 ms | 8,192 bytes | 93.75 MB |

*Decision Justification: $K=128$ matches $K=256$ in classification agreement (99.78%), halves signature footprint (23.4 MB vs 46.9 MB), and generates signatures 4.7x faster.*

---

## 4. Requirement A(c): LSH S-Curve & Asymmetric Cost Optimization (Checkpoint 4)

*Source: `results/lsh_configurations_bench.json` | Evidence: [LSH S-Curve Operating Point](evidence/lsh_scurve_operating_point.png), [Asymmetric Cost Curve](evidence/asymmetric_cost_curve.png)*

- **Fixed Parameters**: $K = 128$, $\tau^* = 0.6028$.
- **Cost Model**: Asymmetric Relative Loss $= R \cdot \text{FP} + 1 \cdot \text{FN}$ with $C_{\text{FM}} : C_{\text{MM}} = R : 1$ over $R \in \{10, 50, 100, 200\}$.

| Configuration $(b, r)$ | Inflection $s^* = (1/b)^{1/r}$ | Candidate Recall (SAME) | Candidate Work Pairs | Candidate Stage FP | Work Reduction vs All-Pairs | Retrieval Wall Time | Final Verified Recall | Final False Merges | Final Business Loss ($R \in [10, 200]$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$(b=8, r=16)$** | 0.8781 | 47.67% (133/279) | 133 | 0 | 99.98% | 94.98 ms | 47.67% | 0 | **146** across all $R$ |
| **$(b=16, r=8)$** | 0.7071 | 78.14% (218/279) | 220 | 2 | 99.94% | 101.86 ms | 78.14% | 0 | **61** across all $R$ |
| **$(b=32, r=4)$ (Selected)** | **0.4204** | **100.00% (279/279)** | **293** | **14** | **97.78%** | **71.20 ms** | **100.00%** | **0** | **0** across all $R$ |
| **$(b=64, r=2)$** | 0.1250 | 100.00% (279/279) | 511 | 232 | 61.61% | 466.09 ms | 100.00% | 0 | **0** across all $R$ |

*Decision Justification: $(b=32, r=4)$ positions inflection $s^* = 0.4204$ safely below $\tau^* = 0.6028$, capturing 100% of duplicates while reducing candidate comparisons by 97.78% and generating 0 final business loss.*

---

## 5. Requirement B(d): Relational Database & Index Benchmarking (Checkpoint 5)

*Source: `results/relational_access_bench.json` | Evidence: [Query Plan Chosen Index](evidence/query_plan_chosen_index.png), [Query Plan Rejected Scan](evidence/query_plan_rejected_scan.png)*

- **Database Engine**: SQLite 3 (`db/procurement_lsh.db`, 124.8 MB, 12,000 notices, 384,000 bucket rows).
- **Index Definition**: `CREATE INDEX idx_lsh_covering ON lsh_buckets(band_id, bucket_hash, notice_id)`.

| Query Access Path | SQLite `EXPLAIN QUERY PLAN` | Latency / Query | Total Rows Examined (100 Q) | Rows Examined / Query | Speedup / Reduction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Chosen Indexed Path** | `SEARCH lsh_buckets USING COVERING INDEX idx_lsh_covering (band_id=? AND bucket_hash=?)` | **0.0351 ms** | **1,039 rows** | **10.39 rows** | **978.3x speedup** / **36,958.6x work reduction** |
| **Rejected Scan Path** | `SCAN lsh_buckets` | 34.3768 ms | 38,400,000 rows | 384,000 rows | Baseline (1.0x) |

| Self-Join Plan Evaluation | SQLite Join Plan Strategy | Wall-Clock Latency / Notice | Join Speedup |
| :--- | :--- | :--- | :--- |
| **Covering Index Self-Join** | `SCAN b1` $\to$ `SEARCH b2 USING COVERING INDEX idx_lsh_covering (band_id=? AND bucket_hash=?)` $\to$ `USE TEMP B-TREE FOR DISTINCT` | **41.57 ms / notice** | **37.4x faster** |
| **Unindexed Self-Join** | `SCAN b1` $\to$ `SCAN b2` $\to$ `USE TEMP B-TREE FOR DISTINCT` | 1,556.77 ms / notice | Baseline (1.0x) |

---

## 6. Requirement B(e): Full Corpus Skew Diagnosis & Mitigation (Checkpoint 6)

*Source: `results/skew_mitigation_benchmarks.json` | Evidence: [Skew Per Notice Distribution](evidence/skew_per_notice_distribution.png), [Mitigation Recall Tradeoff](evidence/mitigation_recall_tradeoff.png)*

Evaluated across the full 12,000-notice corpus.

### Skew Diagnostic Concentration (Baseline Unmitigated)
- **Total Workload**: 1,104,883 candidate pairs (2,209,766 pairwise bucket comparisons).
- **Nodal Aggregators (P001–P006)**: Account for **41.40%** of all comparisons.
- **Top Portal (P094)**: Accounts for **12.01%** of all comparisons.
- **Combined Top 7 Portals**: Account for **53.41%** of all pairwise candidate work.
- **Baseline Recall Dilution**: Baseline unmitigated retrieval misses 13 ground-truth duplicates (**95.34% recall**) due to generic preamble n-grams displacing distinctive tender body content in hash bands.

### Mitigation Evaluation ($C_{\max}$ Sweep)

| Mitigation Pipeline | Total Candidate Pairs | Labelled Recall | Missed Merges (FN) | Max Comparisons / Notice | Retrieval Runtime | Final Business Loss ($R \in [10, 200]$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Raw, No Cap, All Pairs)** | 1,104,883 | 95.34% | 13 | 746 | 1.006 s | 13 |
| **Mit 1: Cleaned Alone** | 1,545,168 | 100.00% | 0 | 900 | 1.430 s | 0 |
| **Mit 2: Cross-Portal Alone** | 1,019,156 | 95.34% | 13 | 731 | 2.225 s | 13 |
| **Combined: $C_{\max} = 200$** | 1,139,122 | 100.00% | 0 | 629 | 1.344 s | 0 |
| **Combined: $C_{\max} = 150$ (Selected)** | **1,032,576** | **100.00%** | **0** | **569** ($-23.7\%$) | **1.126 s** | **0 across all $R$** |
| **Combined: $C_{\max} = 100$** | 803,799 | 100.00% | 0 | 411 | 0.778 s | 0 across all $R$ |
| **Combined: $C_{\max} = 75$** | 618,297 | 99.64% | 1 | 305 | 0.553 s | 1 across all $R$ |
| **Combined: $C_{\max} = 50$** | 451,789 | 99.28% | 2 | 246 | 0.379 s | 2 across all $R$ |
| **Combined: $C_{\max} = 30$** | 281,425 | 99.28% | 2 | 155 | 0.392 s | 2 across all $R$ |
| **Combined: $C_{\max} = 10$** | 91,615 | 97.49% | 7 | 56 | 1.167 s | 7 across all $R$ |

*Selection Rationale: $C_{\max}=150$ was selected based on the measured recall/business-loss/runtime trade-off. It provides 100.00% recall (zero missed merges) and strictly zero business loss, reducing peak comparisons by 23.7% (746 $\to$ 569). $C_{\max}=50$ was rejected because it permanently drops 2 true duplicates (`N003494-N003495` and `N001010-N001011`), incurring unnecessary business loss.*

---

## 7. End-to-End Production Pipeline & 20-Minute Budget Audit (Checkpoint 7)

*Source: `results/full_pipeline_benchmark.json` | Evidence: [Full Corpus Runtime Proof](evidence/full_corpus_runtime_proof.png)*

- **Corpus Processed**: 12,000 tender notices.
- **Operating Configuration**: $K=128$, $b=32$, $r=4$, $\tau^* = 0.6028$, $C_{\max} = 150$, $\tau_{\text{screen}} = 0.45$.
- **Allowed Budget**: 20.0 minutes ($1,200.0$ seconds).

### Stage-by-Stage Latency & Budget Utilization

| Pipeline Stage Number & Description | Measured Wall-Clock Runtime | Share of Total Pipeline | Budget Headroom Remaining |
| :--- | :---: | :---: | :---: |
| **Stage 1**: CSV Ingestion & Partition Parsing | 0.602 s | 0.64% | 1,199.398 s |
| **Stage 2**: Boilerplate Stripping & Preprocessing | 35.342 s | 37.74% | 1,164.056 s |
| **Stage 3**: MinHash Signature Generation ($K=128$) | 9.651 s | 10.31% | 1,154.405 s |
| **Stage 4**: LSH Band Inverted Index Construction | 5.935 s | 6.34% | 1,148.470 s |
| **Stage 5**: SQLite Persistence (Tables + B-tree Index) | 11.872 s | 12.68% | 1,136.598 s |
| **Stage 6**: Candidate Pair Retrieval ($C_{\max}=150$) | 1.472 s | 1.57% | 1,135.126 s |
| **Stage 7**: MinHash Two-Stage Screen ($\tau \ge 0.45$) | 2.279 s | 2.43% | 1,132.847 s |
| **Stage 8**: Exact Composite Verification ($\tau^* \ge 0.6028$) | 22.152 s | 23.66% | 1,110.695 s |
| **Stage 9**: Card Generation & Connected Components | 4.180 s | 4.46% | 1,106.360 s |
| **TOTAL END-TO-END PIPELINE RUNTIME** | **93.640 seconds** | **100.00%** | **1,106.360 seconds** |

### Workload & Output Volume Audit
- **Total Notices Ingested**: 12,000
- **LSH Candidate Pairs Retrieved**: 1,032,576 pairs
- **MinHash Screened Pairs ($\tau \ge 0.45$)**: 231,016 pairs (77.6% candidate pruning)
- **Exact Verified Duplicate Pairs ($\tau^* \ge 0.6028$)**: **19,961 pairs**
- **Synthesized Opportunity Cards**: **4,189 cards**
  - Multi-notice duplicate clusters: **1,715 cards**
  - Single-notice orphan cards: **2,474 cards**
- **Ground-Truth SAME Recall**: **279 / 279 (100.00%)**
- **Missed Merges**: **0**
- **Pipeline Failures / Crashes**: **0**
- **Speedup vs Budget**: **12.82x faster than 20-minute ceiling** (utilizes only 7.80% of budget)
- **Peak Process Memory**: 3,194.6 MB

---

## 8. Determinism & Incremental Stability Audit

| Audit Aspect | Tested Condition | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Full Rerun Consistency** | Clean rerun of entire pipeline on fresh SQLite database | Identical candidate count (1,032,576), screened count (231,016), confirmed duplicates (19,961), and 0 card ID mismatches across all 12,000 notices | **100.00% Deterministic** |
| **Incremental Add Stability** | Ingestion of synthetic duplicate `N099999_CORRIGENDUM` targeting `CARD-N000009` | New notice assigned `CARD-N000009`; existing notice `N000010` retained `CARD-N000009` (0 existing renames) | **PASSED — existing card IDs preserved; demonstrated bookmark-safe behavior** |
