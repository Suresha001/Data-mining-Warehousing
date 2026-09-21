#!/usr/bin/env python3
"""
Question-2: Similarity Calculator
Implements Jaccard similarity and composite multi-field scoring.
"""

from typing import Set
from .preprocessor import get_choice1_shingles, get_choice2_shingle_sets


def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """
    Computes exact Jaccard similarity between two sets:
    J(A, B) = |A ∩ B| / |A ∪ B|. Returns 0.0 if both sets are empty.
    """
    if not set_a or not set_b:
        return 0.0
    intersection_len = len(set_a.intersection(set_b))
    if intersection_len == 0:
        return 0.0
    union_len = len(set_a.union(set_b))
    return intersection_len / union_len


def compute_choice1_similarity(title_a: str, body_a: str, title_b: str, body_b: str) -> float:
    """
    Choice 1: Exact Jaccard similarity of raw word 3-grams over uncleaned title + body.
    """
    sa = get_choice1_shingles(title_a, body_a)
    sb = get_choice1_shingles(title_b, body_b)
    return jaccard_similarity(sa, sb)


def compute_choice2_similarity(title_a: str, body_a: str, title_b: str, body_b: str, alpha: float = 0.5) -> float:
    """
    Choice 2: Composite Jaccard similarity:
    S(A, B) = alpha * J(Title_2grams) + (1 - alpha) * J(Body_3grams)
    using cleaned and normalized fields.
    """
    st_a, sb_a = get_choice2_shingle_sets(title_a, body_a)
    st_b, sb_b = get_choice2_shingle_sets(title_b, body_b)
    
    jt = jaccard_similarity(st_a, st_b)
    jb = jaccard_similarity(sb_a, sb_b)
    
    return alpha * jt + (1.0 - alpha) * jb
