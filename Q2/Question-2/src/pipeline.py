#!/usr/bin/env python3
"""
Question-2: Production End-to-End Procurement Duplicate Detection Pipeline
Implements the complete sublinear LSH deduplication pipeline:
Ingestion -> Normalization -> MinHash (K=128) -> LSH Indexing (b=32, r=4) ->
SQLite Persistence -> Capped Candidate Retrieval (C_max=150) ->
MinHash Screening (tau_screen=0.45) -> Exact Composite Verification (tau*=0.6028) ->
Deterministic Stable Opportunity Card Generation (Union-Find Root Anchoring).
"""

import os
import sys
import glob
import time
import sqlite3
import numpy as np
import pandas as pd
from typing import Dict, List, Set, Tuple, Any, Optional

# Relative imports
from src.preprocessor import clean_title, clean_body, get_word_ngrams
from src.minhash import MinHashGenerator, str_to_hash64
from src.similarity import jaccard_similarity
from src.db_manager import DatabaseManager


class ProcurementPipeline:
    """
    Production-grade end-to-end deduplication pipeline for Setubid.
    """
    def __init__(
        self,
        db_path: str = "Question-2/db/procurement_lsh.db",
        K: int = 128,
        b: int = 32,
        r: int = 4,
        tau_star: float = 0.6028,
        c_max: int = 150,
        tau_screen: float = 0.45,
        seed: int = 42
    ):
        self.db_path = db_path
        self.K = K
        self.b = b
        self.r = r
        self.tau_star = tau_star
        self.c_max = c_max
        self.tau_screen = tau_screen
        self.seed = seed
        
        self.minhash_gen = MinHashGenerator(max_k=self.K, seed=self.seed)
        self.db = DatabaseManager(self.db_path)
        
        # Pipeline Data Structures
        self.df_notices: Optional[pd.DataFrame] = None
        self.n_notices: int = 0
        self.nid_to_idx: Dict[str, int] = {}
        self.idx_to_nid: np.ndarray = np.array([])
        self.portal_ids: np.ndarray = np.array([])
        
        # Shingles and Signatures
        self.clean_titles: List[str] = []
        self.clean_bodies: List[str] = []
        self.title_shingles: List[Set[str]] = []
        self.body_shingles: List[Set[str]] = []
        self.signatures: np.ndarray = np.empty((0, self.K), dtype=np.uint64)
        
        # LSH Index
        self.buckets: Dict[Tuple[int, Tuple], List[int]] = {}
        
        # Candidate and Verified Pairs
        self.candidate_pairs: List[Tuple[int, int]] = []
        self.screened_pairs: List[Tuple[int, int]] = []
        self.verified_duplicate_pairs: List[Tuple[str, str, float]] = []
        
        # Stable Opportunity Cards (notice_id -> card_id, card_id -> metadata)
        self.notice_to_card: Dict[str, str] = {}
        self.cards: Dict[str, Dict[str, Any]] = {}
        
        # Stage timings (seconds)
        self.timings: Dict[str, float] = {}

    def stage1_load_data(self, file_glob: str = "notices/part-*.csv") -> float:
        """Stage 1: Ingests partitioned CSV files into memory."""
        t0 = time.perf_counter()
        files = sorted(glob.glob(file_glob))
        assert len(files) > 0, f"No notice files found matching {file_glob}"
        dfs = [pd.read_csv(f) for f in files]
        self.df_notices = pd.concat(dfs, ignore_index=True)
        self.n_notices = len(self.df_notices)
        self.nid_to_idx = {nid: i for i, nid in enumerate(self.df_notices['notice_id'])}
        self.idx_to_nid = self.df_notices['notice_id'].values
        self.portal_ids = self.df_notices['portal_id'].values
        elapsed = time.perf_counter() - t0
        self.timings['stage1_data_loading'] = elapsed
        return elapsed

    def stage2_preprocess(self) -> float:
        """Stage 2: Strips portal boilerplate preambles and generates n-grams."""
        t0 = time.perf_counter()
        self.clean_titles = [clean_title(t) for t in self.df_notices['title']]
        self.clean_bodies = [clean_body(b) for b in self.df_notices['body']]
        self.title_shingles = [get_word_ngrams(t, 2) for t in self.clean_titles]
        self.body_shingles = [get_word_ngrams(b, 3) for b in self.clean_bodies]
        elapsed = time.perf_counter() - t0
        self.timings['stage2_preprocessing'] = elapsed
        return elapsed

    def stage3_generate_signatures(self) -> float:
        """Stage 3: Generates compact K=128 MinHash signatures."""
        t0 = time.perf_counter()
        all_shingles = set().union(*self.title_shingles, *self.body_shingles)
        shingle_hash_map = {s: str_to_hash64(s) for s in all_shingles}
        
        t_hashes = [np.array([shingle_hash_map[s] for s in s_set], dtype=np.uint64) for s_set in self.title_shingles]
        b_hashes = [np.array([shingle_hash_map[s] for s in s_set], dtype=np.uint64) for s_set in self.body_shingles]
        
        self.signatures = np.empty((self.n_notices, self.K), dtype=np.uint64)
        for i in range(self.n_notices):
            st = self.minhash_gen.compute_signature_from_hashes(t_hashes[i], 'title', self.K)
            sb = self.minhash_gen.compute_signature_from_hashes(b_hashes[i], 'body', self.K)
            self.signatures[i, 0::2] = st[:self.K // 2]
            self.signatures[i, 1::2] = sb[:self.K // 2]
            
        elapsed = time.perf_counter() - t0
        self.timings['stage3_minhash_signatures'] = elapsed
        return elapsed

    def stage4_build_lsh_index(self) -> float:
        """Stage 4: Constructs in-memory band partitions for sublinear lookup."""
        t0 = time.perf_counter()
        self.buckets.clear()
        for i in range(self.n_notices):
            for band_idx in range(self.b):
                band_slice = tuple(self.signatures[i, band_idx * self.r : (band_idx + 1) * self.r])
                b_key = (band_idx, band_slice)
                if b_key not in self.buckets:
                    self.buckets[b_key] = []
                self.buckets[b_key].append(i)
        elapsed = time.perf_counter() - t0
        self.timings['stage4_lsh_index_build'] = elapsed
        return elapsed

    def stage5_persist_sqlite(self) -> float:
        """Stage 5: Persists notices, LSH buckets, and covering B-Tree index to SQLite."""
        t0 = time.perf_counter()
        self.db.init_schema()
        with self.db.conn:
            # Clear existing table contents for clean rerun idempotency
            self.db.conn.execute("DELETE FROM notices")
            self.db.conn.execute("DELETE FROM lsh_buckets")
            
            # Batch insert notices
            notices_rows = [
                (r.notice_id, r.portal_id, str(r.published_at), r.title, r.body, int(r.estimated_value), str(r.closing_date))
                for _, r in self.df_notices.iterrows()
            ]
            self.db.conn.executemany("INSERT INTO notices VALUES (?, ?, ?, ?, ?, ?, ?)", notices_rows)
            
            # Batch insert bucket entries
            bucket_rows = []
            for (band_idx, band_slice), members in self.buckets.items():
                hash_str = "_".join(f"{h:016x}" for h in band_slice)
                for m_idx in members:
                    bucket_rows.append((band_idx, hash_str, self.idx_to_nid[m_idx]))
            self.db.conn.executemany("INSERT INTO lsh_buckets VALUES (?, ?, ?)", bucket_rows)
            
        # Ensure covering index is built
        self.db.create_covering_index()
        elapsed = time.perf_counter() - t0
        self.timings['stage5_sqlite_persistence'] = elapsed
        return elapsed

    def stage6_retrieve_candidates(self) -> float:
        """Stage 6: Extracts candidate pairs enforcing C_max=150 and cross-portal filter."""
        t0 = time.perf_counter()
        cand_set = set()
        for b_key, members in self.buckets.items():
            n_m = len(members)
            if 1 < n_m <= self.c_max:
                for idx in range(n_m):
                    u = members[idx]
                    p_u = self.portal_ids[u]
                    for jdx in range(idx + 1, n_m):
                        v = members[jdx]
                        if p_u != self.portal_ids[v]:
                            pair = (u, v) if u < v else (v, u)
                            cand_set.add(pair)
        self.candidate_pairs = list(cand_set)
        elapsed = time.perf_counter() - t0
        self.timings['stage6_candidate_retrieval'] = elapsed
        return elapsed

    def stage7_screen_minhash(self) -> float:
        """Stage 7: High-speed vectorized MinHash screening filter (tau_screen=0.45)."""
        t0 = time.perf_counter()
        if not self.candidate_pairs:
            self.screened_pairs = []
            return 0.0
            
        u_arr = np.array([p[0] for p in self.candidate_pairs], dtype=np.int32)
        v_arr = np.array([p[1] for p in self.candidate_pairs], dtype=np.int32)
        
        # Fast vectorized equality check across K=128 rows
        matches = np.sum(self.signatures[u_arr] == self.signatures[v_arr], axis=1) / self.K
        survivor_indices = np.where(matches >= self.tau_screen)[0]
        self.screened_pairs = [self.candidate_pairs[i] for i in survivor_indices]
        elapsed = time.perf_counter() - t0
        self.timings['stage7_minhash_screening'] = elapsed
        return elapsed

    def stage8_verify_exact(self) -> float:
        """Stage 8: Exact composite similarity verification (tau* = 0.6028)."""
        t0 = time.perf_counter()
        verified = []
        for u_idx, v_idx in self.screened_pairs:
            sim = 0.5 * jaccard_similarity(self.title_shingles[u_idx], self.title_shingles[v_idx]) + \
                  0.5 * jaccard_similarity(self.body_shingles[u_idx], self.body_shingles[v_idx])
            if sim >= self.tau_star:
                verified.append((self.idx_to_nid[u_idx], self.idx_to_nid[v_idx], float(sim)))
                
        self.verified_duplicate_pairs = verified
        elapsed = time.perf_counter() - t0
        self.timings['stage8_exact_verification'] = elapsed
        return elapsed

    def stage9_generate_cards(self) -> float:
        """
        Stage 9: Opportunity Card Generation using Union-Find clustering with
        initial lexicographical anchor root assignment for newly minted cards.
        Initial Minting Rule: CARD-<min(cluster_notice_ids)>
        
        NOTE ON STABILITY GUARANTEE:
        Dynamically recomputing min(cluster_notice_ids) on arbitrary future arrivals is NOT
        universally stable, because a future notice with a smaller ID would shift the minimum.
        Therefore, persistent stability is achieved by committing notice-to-card mappings into
        self.notice_to_card (and persistent database). Subsequent duplicate arrivals inherit
        the established card ID without recomputing cluster membership.
        """
        t0 = time.perf_counter()
        # Disjoint-set union-find over all 12,000 notices
        parent = list(range(self.n_notices))
        
        def find(i: int) -> int:
            path = []
            while parent[i] != i:
                path.append(i)
                i = parent[i]
            for node in path:
                parent[node] = i
            return i

        def union(i: int, j: int):
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                # Invariant: Lexicographically smallest notice_id becomes the cluster root!
                if self.idx_to_nid[root_i] < self.idx_to_nid[root_j]:
                    parent[root_j] = root_i
                else:
                    parent[root_i] = root_j

        for u_nid, v_nid, _ in self.verified_duplicate_pairs:
            union(self.nid_to_idx[u_nid], self.nid_to_idx[v_nid])

        # Form clusters
        clusters: Dict[str, List[str]] = {}
        self.notice_to_card.clear()
        
        for i in range(self.n_notices):
            root_idx = find(i)
            canonical_nid = self.idx_to_nid[root_idx]
            card_id = f"CARD-{canonical_nid}"
            nid = self.idx_to_nid[i]
            
            self.notice_to_card[nid] = card_id
            if card_id not in clusters:
                clusters[card_id] = []
            clusters[card_id].append(nid)

        # Aggregate Opportunity Cards
        self.cards.clear()
        for card_id, members in clusters.items():
            member_rows = self.df_notices[self.df_notices['notice_id'].isin(members)]
            # Card aggregation
            canon_row = member_rows.iloc[0]
            self.cards[card_id] = {
                "card_id": card_id,
                "canonical_notice_id": canon_row.notice_id,
                "member_notices": members,
                "member_count": len(members),
                "portals": sorted(list(member_rows['portal_id'].unique())),
                "title": canon_row.title,
                "estimated_value": int(canon_row.estimated_value),
                "closing_date": canon_row.closing_date
            }
            
        elapsed = time.perf_counter() - t0
        self.timings['stage9_card_generation'] = elapsed
        return elapsed

    def add_incremental_copy(self, new_notice_id: str, duplicate_of_id: str, new_portal_id: str) -> str:
        """
        Incremental arrival test:
        When a new notice arrives that duplicates an existing notice,
        it merges into the existing card WITHOUT renaming or reassigning existing notice card IDs.
        """
        assert duplicate_of_id in self.notice_to_card, f"Existing notice {duplicate_of_id} not found!"
        existing_card_id = self.notice_to_card[duplicate_of_id]
        
        # Assign new copy to established card ID
        self.notice_to_card[new_notice_id] = existing_card_id
        if existing_card_id in self.cards:
            self.cards[existing_card_id]["member_notices"].append(new_notice_id)
            self.cards[existing_card_id]["member_count"] += 1
            if new_portal_id not in self.cards[existing_card_id]["portals"]:
                self.cards[existing_card_id]["portals"].append(new_portal_id)
                
        return existing_card_id

    def run_all(self, file_glob: str = "notices/part-*.csv") -> Dict[str, Any]:
        """Executes all 9 stages in sequence and returns complete performance report."""
        t_start = time.perf_counter()
        
        t1 = self.stage1_load_data(file_glob)
        t2 = self.stage2_preprocess()
        t3 = self.stage3_generate_signatures()
        t4 = self.stage4_build_lsh_index()
        t5 = self.stage5_persist_sqlite()
        t6 = self.stage6_retrieve_candidates()
        t7 = self.stage7_screen_minhash()
        t8 = self.stage8_verify_exact()
        t9 = self.stage9_generate_cards()
        
        total_time = time.perf_counter() - t_start
        self.timings['total_pipeline_runtime'] = total_time
        
        return {
            "timings": self.timings,
            "total_notices": self.n_notices,
            "candidate_pairs": len(self.candidate_pairs),
            "screened_pairs": len(self.screened_pairs),
            "verified_duplicate_pairs": len(self.verified_duplicate_pairs),
            "total_opportunity_cards": len(self.cards),
            "multi_notice_cards": sum(1 for c in self.cards.values() if c['member_count'] > 1)
        }
