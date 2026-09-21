import sys, glob, time, json, os
import pandas as pd
import numpy as np

sys.path.insert(0, 'Question-2')
from src.preprocessor import get_word_ngrams, clean_title, clean_body
from src.minhash import MinHashGenerator, str_to_hash64

# Load notices and labels
dfs = [pd.read_csv(f) for f in sorted(glob.glob('notices/part-*.csv'))]
df = pd.concat(dfs, ignore_index=True)
df_labels = pd.read_csv('labelled_pairs.csv')
same_pairs = set(tuple(sorted((r.notice_id_a, r.notice_id_b))) for _, r in df_labels[df_labels['label'] == 'same'].iterrows())
print(f'Total SAME labelled pairs to recall: {len(same_pairs)}')

n_notices = len(df)
nid_to_idx = {nid: i for i, nid in enumerate(df['notice_id'])}
idx_to_nid = df['notice_id'].values
portal_ids = df['portal_id'].values
K = 128
b = 32
r = 4
minhash_gen = MinHashGenerator(max_k=K, seed=42)

print("Computing Raw signatures...")
t0 = time.perf_counter()
raw_t_s = [get_word_ngrams(str(t).lower(), 2) for t in df['title']]
raw_b_s = [get_word_ngrams(str(b).lower(), 3) for b in df['body']]
all_raw_s = set().union(*raw_t_s, *raw_b_s)
raw_hash_map = {s: str_to_hash64(s) for s in all_raw_s}
raw_t_h = [np.array([raw_hash_map[s] for s in s_set], dtype=np.uint64) for s_set in raw_t_s]
raw_b_h = [np.array([raw_hash_map[s] for s in s_set], dtype=np.uint64) for s_set in raw_b_s]

sig_raw = np.empty((n_notices, K), dtype=np.uint64)
for i in range(n_notices):
    st = minhash_gen.compute_signature_from_hashes(raw_t_h[i], 'title', K)
    sb = minhash_gen.compute_signature_from_hashes(raw_b_h[i], 'body', K)
    sig_raw[i, 0::2] = st[:K//2]
    sig_raw[i, 1::2] = sb[:K//2]
print(f"Raw signatures generated in {time.perf_counter()-t0:.2f}s")

print("Computing Clean signatures...")
t0 = time.perf_counter()
clean_t_s = [get_word_ngrams(clean_title(t), 2) for t in df['title']]
clean_b_s = [get_word_ngrams(clean_body(b), 3) for b in df['body']]
all_clean_s = set().union(*clean_t_s, *clean_b_s)
clean_hash_map = {s: str_to_hash64(s) for s in all_clean_s}
clean_t_h = [np.array([clean_hash_map[s] for s in s_set], dtype=np.uint64) for s_set in clean_t_s]
clean_b_h = [np.array([clean_hash_map[s] for s in s_set], dtype=np.uint64) for s_set in clean_b_s]

sig_clean = np.empty((n_notices, K), dtype=np.uint64)
for i in range(n_notices):
    st = minhash_gen.compute_signature_from_hashes(clean_t_h[i], 'title', K)
    sb = minhash_gen.compute_signature_from_hashes(clean_b_h[i], 'body', K)
    sig_clean[i, 0::2] = st[:K//2]
    sig_clean[i, 1::2] = sb[:K//2]
print(f"Clean signatures generated in {time.perf_counter()-t0:.2f}s")

def evaluate_retrieval(signatures, name, cross_portal=False, max_bucket_size=None):
    t0 = time.perf_counter()
    # Build buckets
    buckets = {}
    for i in range(n_notices):
        for band_idx in range(b):
            band_slice = tuple(signatures[i, band_idx * r : (band_idx + 1) * r])
            b_key = (band_idx, band_slice)
            if b_key not in buckets:
                buckets[b_key] = []
            buckets[b_key].append(i)
            
    # Retrieve pairs
    adj = [set() for _ in range(n_notices)]
    candidate_pairs = set()
    
    for b_key, members in buckets.items():
        if len(members) <= 1:
            continue
        if max_bucket_size is not None and len(members) > max_bucket_size:
            continue
            
        n_m = len(members)
        for idx in range(n_m):
            u = members[idx]
            p_u = portal_ids[u]
            for jdx in range(idx + 1, n_m):
                v = members[jdx]
                p_v = portal_ids[v]
                if cross_portal and p_u == p_v:
                    continue
                pair = (u, v) if u < v else (v, u)
                candidate_pairs.add(pair)
                adj[u].add(v)
                adj[v].add(u)
                
    wall_time = time.perf_counter() - t0
    degrees = np.array([len(s) for s in adj])
    total_pairs = len(candidate_pairs)
    
    # Check recall on labelled SAME pairs
    recalled = 0
    for u_nid, v_nid in same_pairs:
        if u_nid in nid_to_idx and v_nid in nid_to_idx:
            u_idx = nid_to_idx[u_nid]
            v_idx = nid_to_idx[v_nid]
            pair = (u_idx, v_idx) if u_idx < v_idx else (v_idx, u_idx)
            if pair in candidate_pairs:
                recalled += 1
    recall = recalled / len(same_pairs)
    
    p50 = float(np.percentile(degrees, 50))
    p90 = float(np.percentile(degrees, 90))
    p95 = float(np.percentile(degrees, 95))
    p99 = float(np.percentile(degrees, 99))
    max_w = int(np.max(degrees))
    
    print(f"[{name}]")
    print(f"  Time: {wall_time:.3f}s | Pairs: {total_pairs:,} | Recall: {recalled}/{len(same_pairs)} ({recall*100:.2f}%)")
    print(f"  Work dist: p50={p50:.1f}, p90={p90:.1f}, p95={p95:.1f}, p99={p99:.1f}, max={max_w}")
    return {
        "name": name,
        "time": wall_time,
        "total_pairs": total_pairs,
        "recalled": recalled,
        "recall": recall,
        "degrees": degrees,
        "p50": p50,
        "p90": p90,
        "p95": p95,
        "p99": p99,
        "max": max_w
    }

print("\n--- BENCHMARKING VARIANTS ---")
res_baseline = evaluate_retrieval(sig_raw, "Baseline (Raw, No Cap, All Pairs)", cross_portal=False, max_bucket_size=None)
res_m1 = evaluate_retrieval(sig_clean, "Mitigation 1 (Clean/Stripped, No Cap, All Pairs)", cross_portal=False, max_bucket_size=None)
res_m2 = evaluate_retrieval(sig_raw, "Mitigation 2 (Raw, No Cap, Cross-Portal Only)", cross_portal=True, max_bucket_size=None)
res_m12 = evaluate_retrieval(sig_clean, "Mitigation 1+2 (Clean, No Cap, Cross-Portal Only)", cross_portal=True, max_bucket_size=None)

# Bucket capping exploration on Clean + Cross-portal
for cap in [300, 200, 150, 100, 50]:
    evaluate_retrieval(sig_clean, f"Clean + Cross-Portal + Cap={cap}", cross_portal=True, max_bucket_size=cap)
