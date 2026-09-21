#!/usr/bin/env python3
"""
Question-2: Locality-Sensitive Hashing (LSH) Engine
Implements sublinear candidate pair retrieval using band partitioning.
Maps signatures into b bands of r rows each (K = b * r) and extracts
candidate pairs that collide in at least one band.
"""

from typing import Dict, List, Set, Tuple
import numpy as np


class LSHIndex:
    """
    In-memory LSH Index using band hashing over compact MinHash signatures.
    """
    def __init__(self, b: int, r: int):
        self.b = b
        self.r = r
        self.K = b * r
        # Buckets: key = (band_id, tuple_of_r_hashes), value = list of notice_ids
        self.buckets: Dict[Tuple[int, Tuple], List[str]] = {}
        self.indexed_notices: Set[str] = set()

    def add_notice(self, notice_id: str, signature: np.ndarray):
        """
        Partitions the notice's signature into b bands of r rows and indexes it.
        """
        assert len(signature) >= self.K, f"Signature length {len(signature)} < required K={self.K}"
        self.indexed_notices.add(notice_id)
        for band_idx in range(self.b):
            band_slice = tuple(signature[band_idx * self.r : (band_idx + 1) * self.r])
            bucket_key = (band_idx, band_slice)
            if bucket_key not in self.buckets:
                self.buckets[bucket_key] = []
            self.buckets[bucket_key].append(notice_id)

    def get_candidate_pairs(self) -> Set[Tuple[str, str]]:
        """
        Retrieves all unique candidate pairs that share a bucket in at least one band.
        Pairs are sorted alphabetically (id_a < id_b).
        """
        candidate_pairs = set()
        for members in self.buckets.values():
            if len(members) > 1:
                n = len(members)
                for i in range(n):
                    for j in range(i + 1, n):
                        pair = (members[i], members[j]) if members[i] < members[j] else (members[j], members[i])
                        candidate_pairs.add(pair)
        return candidate_pairs

    def check_pair_collision(self, sig_a: np.ndarray, sig_b: np.ndarray) -> bool:
        """
        Checks if two signatures collide in at least one band.
        """
        for band_idx in range(self.b):
            start = band_idx * self.r
            end = start + self.r
            if np.array_equal(sig_a[start:end], sig_b[start:end]):
                return True
        return False
