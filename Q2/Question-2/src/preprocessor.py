#!/usr/bin/env python3
"""
Question-2: Text Preprocessor & Normalizer
Extracts clean, high-signal tokens and shingles from tender titles and bodies.
Strips portal boilerplate preambles, disclaimers, reference patterns,
and normalizes casing and punctuation.
"""

import re
from typing import Set, Tuple

# Pre-compiled regex patterns for performance
RE_TITLE_PREFIX = re.compile(
    r'^(tender\s+notice:?\s*|e-tender\s*-\s*|nit\s+for\s*|corrigendum\s*-\s*)+',
    re.IGNORECASE
)
RE_BRACKETS = re.compile(r'\[.*?\]')
RE_TRAILING_DISTRICT = re.compile(r'\s*-\s*[a-zA-Z\s]+$')

# Nodal Aggregator Preambles
RE_NODAL_A_PREAMBLE = re.compile(
    r'GOVERNMENT OF INDIA -- NATIONAL PROCUREMENT AGGREGATION SERVICE.*?STANDARD TERMS AND CONDITIONS.*?(\n\n|===============================================================================|$)',
    re.DOTALL
)
RE_NODAL_B_PREAMBLE = re.compile(
    r'STATE PROCUREMENT CELL -- CONSOLIDATED TENDER BULLETIN.*?GENERAL INSTRUCTIONS TO BIDDERS.*?(\n\n|===============================================================================|$)',
    re.DOTALL
)
RE_DISCLAIMER = re.compile(r'DISCLAIMER:.*?$', re.DOTALL | re.IGNORECASE)

# Synthetic Reference Number Patterns
RE_REF_CODES = re.compile(r'\b(NPAS|SPC|PWD|ref|MC|TN|ZILL|TENDER)[\w\/\-\:]+\b', re.IGNORECASE)
RE_BARE_REF = re.compile(r'\b\d{5,8}\b')

# Token matching
RE_WORDS = re.compile(r'\b[a-zA-Z0-9]+\b')


def clean_title(title: str) -> str:
    """
    Cleans tender title by removing portal prefixes (NIT for, e-Tender, Corrigendum),
    bracketed reference codes, and trailing district suffixes.
    """
    if not title:
        return ""
    t = RE_TITLE_PREFIX.sub('', str(title)).strip()
    t = RE_BRACKETS.sub('', t).strip()
    t = RE_TRAILING_DISTRICT.sub('', t).strip()
    return t.lower()


def clean_body(body: str) -> str:
    """
    Cleans tender body by stripping nodal aggregator legal preambles (~1,400-1,852 chars),
    disclaimer footers, and synthetic portal reference numbers.
    """
    if not body:
        return ""
    t = str(body)
    t = RE_NODAL_A_PREAMBLE.sub('', t)
    t = RE_NODAL_B_PREAMBLE.sub('', t)
    t = RE_DISCLAIMER.sub('', t)
    t = RE_REF_CODES.sub('', t)
    t = RE_BARE_REF.sub('', t)
    return t.lower()


def get_word_ngrams(text: str, n: int) -> Set[str]:
    """
    Decomposes text into a set of word n-grams.
    If text has fewer than n words, returns the full token sequence as a single item.
    """
    words = RE_WORDS.findall(text.lower())
    if not words:
        return set()
    if len(words) < n:
        return {' '.join(words)}
    return {' '.join(words[i:i+n]) for i in range(len(words) - n + 1)}


def get_choice1_shingles(title: str, body: str) -> Set[str]:
    """
    Choice 1 representation: Raw word 3-grams on concatenated title + body.
    No stripping, preserving all preambles, disclaimers, and reference numbers.
    """
    combined = f"{title} {body}"
    return get_word_ngrams(combined, n=3)


def get_choice2_shingle_sets(title: str, body: str) -> Tuple[Set[str], Set[str]]:
    """
    Choice 2 representation:
    Cleaned Title word 2-grams + Cleaned Body Core word 3-grams.
    """
    c_title = clean_title(title)
    c_body = clean_body(body)
    title_shingles = get_word_ngrams(c_title, n=2)
    body_shingles = get_word_ngrams(c_body, n=3)
    return title_shingles, body_shingles
