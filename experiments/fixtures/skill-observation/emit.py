#!/usr/bin/env python3
"""Deterministic noisy diagnostic fixture for a skill behavior pilot."""

import hashlib


for number in range(1, 6001):
    case = hashlib.blake2s(str(number).encode(), digest_size=5).hexdigest()
    if number in (739, 2914, 5682):
        expected = (number * 17) % 97
        observed = expected + 3
        print(f"ASSERTION line={number} case={case} expected={expected} observed={observed}")
    else:
        print(f"trace line={number} case={case} status=ok detail=" + "x" * 90)
