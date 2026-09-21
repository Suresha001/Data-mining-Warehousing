#!/usr/bin/env python3
"""
Question-2: Vectorized Universal MinHash Signature Generator
Implements universal hashing modulo Mersenne Prime (2^61 - 1)
to generate compact K-dimensional integer signatures from shingle sets.
"""

import hashlib
from typing import Set, Dict, Tuple
import numpy as np

MERSENNE_PRIME = (1 << 61) - 1
MAX_HASH = (1 << 61) - 1


def str_to_hash64(s: str) -> int:
    """Hashes a string token to a 61-bit integer."""
    h = hashlib.md5(s.encode('utf-8')).digest()
    return int.from_bytes(h[:8], byteorder='little') & MAX_HASH


class MinHashGenerator:
    """
    Generates vectorized MinHash signatures using independent universal hash functions:
    h_i(x) = (a_i * x + b_i) mod (2^61 - 1).
    """
    def __init__(self, max_k: int = 512, seed: int = 42):
        self.max_k = max_k
        np.random.seed(seed)
        # Random coefficients: a must be positive odd integer, b is non-negative
        self.a_title = np.random.randint(1, MERSENNE_PRIME, size=max_k, dtype=np.uint64) | np.uint64(1)
        self.b_title = np.random.randint(0, MERSENNE_PRIME, size=max_k, dtype=np.uint64)
        self.a_body = np.random.randint(1, MERSENNE_PRIME, size=max_k, dtype=np.uint64) | np.uint64(1)
        self.b_body = np.random.randint(0, MERSENNE_PRIME, size=max_k, dtype=np.uint64)

    def compute_signature_from_hashes(self, int_hashes: np.ndarray, field: str, k: int) -> np.ndarray:
        """
        Computes a k-dimensional signature from pre-hashed 64-bit integer tokens.
        """
        if len(int_hashes) == 0:
            return np.zeros(k, dtype=np.uint64)
        a = self.a_title[:k] if field == 'title' else self.a_body[:k]
        b = self.b_title[:k] if field == 'title' else self.b_body[:k]
        
        # Broadcast multiply and mod: (k, 1) * (1, num_tokens)
        all_h = (a[:, None] * int_hashes[None, :] + b[:, None]) % MERSENNE_PRIME
        return np.min(all_h, axis=1)

    def compute_signature(self, shingles: Set[str], field: str, k: int) -> np.ndarray:
        """Computes a k-dimensional signature from a string set."""
        if not shingles:
            return np.zeros(k, dtype=np.uint64)
        int_hashes = np.array([str_to_hash64(s) for s in shingles], dtype=np.uint64)
        return self.compute_signature_from_hashes(int_hashes, field, k)

    @staticmethod
    def estimate_jaccard(sig_a: np.ndarray, sig_b: np.ndarray) -> float:
        """Estimates single-field Jaccard similarity as the fraction of matching hash values."""
        if len(sig_a) == 0 or len(sig_b) == 0:
            return 0.0
        # If both are empty sentinel vectors (all zeros)
        if np.all(sig_a == 0) or np.all(sig_b == 0):
            return 0.0
        return float(np.mean(sig_a == sig_b))

    @classmethod
    def estimate_composite(
        cls,
        sig_title_a: np.ndarray,
        sig_body_a: np.ndarray,
        sig_title_b: np.ndarray,
        sig_body_b: np.ndarray,
        alpha: float = 0.5
    ) -> float:
        """Estimates multi-field composite similarity: alpha * J_t + (1 - alpha) * J_b."""
        jt = cls.estimate_jaccard(sig_title_a, sig_title_b)
        jb = cls.estimate_jaccard(sig_body_a, sig_body_b)
        return alpha * jt + (1.0 - alpha) * jb
