"""Utility functions for input validation and combination generation."""

import itertools
import random
from typing import Iterable, List, Tuple


MIN_M = 45
MAX_M = 54
MIN_N = 7
MAX_N = 25
MIN_K = 4
MAX_K = 7
MIN_S = 3
MAX_S = 7
LARGE_COMBINATION_WARNING_THRESHOLD = 200000


def _ensure_positive_integer(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be a positive integer.")
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer.")


def validate_parameters(m: int, n: int, k: int, j: int, s: int) -> None:
    """Validate all core parameters.

    Raises:
        ValueError: If any parameter is invalid.
    """
    for value, name in ((m, "m"), (n, "n"), (k, "k"), (j, "j"), (s, "s")):
        _ensure_positive_integer(value, name)

    if m < MIN_M or m > MAX_M:
        raise ValueError(f"m must be between {MIN_M} and {MAX_M}.")
    if n < MIN_N or n > MAX_N:
        raise ValueError(f"n must be between {MIN_N} and {MAX_N}.")
    if n > m:
        raise ValueError("n cannot be greater than m.")
    if k < MIN_K or k > MAX_K:
        raise ValueError(f"k must be between {MIN_K} and {MAX_K}.")
    if k > n:
        raise ValueError("k cannot be greater than n.")
    if s < MIN_S or s > MAX_S:
        raise ValueError(f"s must be between {MIN_S} and {MAX_S}.")
    if j > k:
        raise ValueError("j cannot be greater than k.")
    if s > j:
        raise ValueError("s must be less than or equal to j.")


def choose_samples_randomly(m: int, n: int) -> List[int]:
    """Choose n unique samples from 1..m randomly and return them sorted."""
    _ensure_positive_integer(m, "m")
    _ensure_positive_integer(n, "n")
    if n > m:
        raise ValueError("n cannot be greater than m.")
    return sorted(random.sample(range(1, m + 1), n))


def parse_user_samples(input_text: str, m: int, n: int) -> List[int]:
    """Parse a user supplied sample list.

    The input must contain exactly n positive integers in the range 1..m
    without duplicates. The returned list is sorted to keep output stable.
    """
    _ensure_positive_integer(m, "m")
    _ensure_positive_integer(n, "n")

    tokens = input_text.split()
    if len(tokens) != n:
        raise ValueError(f"Expected exactly {n} samples, but got {len(tokens)}.")

    samples = []
    for token in tokens:
        if not token.isdigit():
            raise ValueError("All samples must be positive integers.")
        value = int(token)
        if value <= 0:
            raise ValueError("All samples must be positive integers.")
        if value < 1 or value > m:
            raise ValueError(f"Sample {value} is outside the valid range 1 to {m}.")
        samples.append(value)

    unique_samples = set(samples)
    if len(unique_samples) != len(samples):
        raise ValueError("Samples cannot contain duplicates.")

    return sorted(samples)


def generate_combinations(samples: Iterable[int], r: int) -> List[Tuple[int, ...]]:
    """Generate all size-r combinations from samples as sorted tuples."""
    _ensure_positive_integer(r, "r")
    sorted_samples = sorted(samples)
    if r > len(sorted_samples):
        raise ValueError("r cannot be greater than the number of samples.")
    return list(itertools.combinations(sorted_samples, r))


def read_positive_integer(prompt: str) -> int:
    """Read a positive integer from stdin until the user provides one."""
    while True:
        raw_value = input(prompt).strip()
        if raw_value.isdigit():
            value = int(raw_value)
            if value > 0:
                return value
        print("Invalid input. Please enter a positive integer.")


def read_yes_no(prompt: str, default: bool = False) -> bool:
    """Read a yes/no answer from stdin."""
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        answer = input(f"{prompt} {suffix}: ").strip().lower()
        if answer == "":
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Invalid input. Please enter y or n.")
