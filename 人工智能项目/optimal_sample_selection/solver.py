"""Core algorithms for the Optimal Samples Selection System."""

import math
import random
import time
from typing import Dict, List, Optional, Sequence, Set, Tuple

from optimal_sample_selection.utils import generate_combinations


Candidate = Tuple[int, ...]
Target = Tuple[int, ...]
CoverageMap = Dict[Candidate, Set[Target]]

DEFAULT_TOP_N = 5


def is_target_covered_by_candidate(target: Target, candidate: Candidate, s: int) -> bool:
    """Return True when target J is covered by candidate K.

    The target is a j-combination that must be covered. The candidate is a
    selected k-combination. The coverage condition is len(J ∩ K) >= s, meaning
    at least s samples overlap between the two combinations.
    """
    return len(set(target) & set(candidate)) >= s


def build_coverage_map(candidates: Sequence[Candidate], targets: Sequence[Target], s: int) -> CoverageMap:
    """Build a candidate-to-target coverage map.

    This is the set-cover model used by the project:
    - each candidate k-combination is a set that can cover multiple targets;
    - each target j-combination is a requirement that must be covered;
    - a target J is covered by candidate K when len(J ∩ K) >= s.
    """
    coverage_map = {}
    target_sets = []
    for target in targets:
        target_sets.append((target, set(target)))

    for candidate in candidates:
        candidate_set = set(candidate)
        covered_targets = set()
        for target, target_set in target_sets:
            if len(candidate_set & target_set) >= s:
                covered_targets.add(target)
        coverage_map[candidate] = covered_targets

    return coverage_map


def greedy_set_cover(
    candidates: Sequence[Candidate],
    targets: Sequence[Target],
    coverage_map: CoverageMap,
    randomized: bool = False,
    top_n: int = DEFAULT_TOP_N,
) -> List[Candidate]:
    """Run greedy set cover and return selected candidate groups.

    At each round the algorithm chooses the candidate that covers the largest
    number of currently uncovered targets. With randomized=True, it chooses
    randomly from the best top_n candidates to produce alternative nearly
    optimal solutions across repeated runs.
    """
    uncovered_targets = set(targets)
    selected_groups = []
    selected_set = set()
    ordered_candidates = sorted(candidates)

    while uncovered_targets:
        scored_candidates = []
        best_gain = 0

        for candidate in ordered_candidates:
            if candidate in selected_set:
                continue
            gain = len(coverage_map[candidate] & uncovered_targets)
            if gain <= 0:
                continue

            if randomized:
                scored_candidates.append((gain, candidate))
                if gain > best_gain:
                    best_gain = gain
            else:
                if gain > best_gain:
                    best_gain = gain
                    scored_candidates = [(gain, candidate)]
                elif gain == best_gain:
                    scored_candidates.append((gain, candidate))

        if not scored_candidates:
            raise RuntimeError("Unable to cover all targets with the generated candidates.")

        if randomized:
            scored_candidates.sort(key=lambda item: (-item[0], item[1]))
            top_candidates = scored_candidates[:max(1, top_n)]
            _, chosen_candidate = random.choice(top_candidates)
        else:
            scored_candidates.sort(key=lambda item: item[1])
            _, chosen_candidate = scored_candidates[0]

        selected_groups.append(chosen_candidate)
        selected_set.add(chosen_candidate)
        uncovered_targets -= coverage_map[chosen_candidate]

    return selected_groups


def check_all_targets_covered(selected_groups: Sequence[Candidate], targets: Sequence[Target], s: int) -> bool:
    """Check whether all targets are covered by the selected k-combinations."""
    selected_group_sets = [set(group) for group in selected_groups]

    for target in targets:
        target_set = set(target)
        target_is_covered = False
        for group_set in selected_group_sets:
            if len(target_set & group_set) >= s:
                target_is_covered = True
                break
        if not target_is_covered:
            return False

    return True


def optimize_by_removing_redundant_groups(
    selected_groups: Sequence[Candidate],
    targets: Sequence[Target],
    s: int,
) -> List[Candidate]:
    """Remove redundant selected groups while preserving complete coverage."""
    optimized_groups = list(selected_groups)
    changed = True

    while changed:
        changed = False
        for group in list(optimized_groups):
            candidate_groups = []
            removed = False
            for existing_group in optimized_groups:
                if existing_group == group and not removed:
                    removed = True
                    continue
                candidate_groups.append(existing_group)

            if candidate_groups and check_all_targets_covered(candidate_groups, targets, s):
                optimized_groups = candidate_groups
                changed = True
                break

    return sorted(optimized_groups)


def _calculate_expected_coverage_count(n: int, k: int, j: int, s: int) -> int:
    total = 0
    upper_bound = min(j, k)
    for intersection_size in range(s, upper_bound + 1):
        remaining_target_size = j - intersection_size
        outside_candidate_count = n - k
        if remaining_target_size > outside_candidate_count:
            continue
        total += math.comb(k, intersection_size) * math.comb(outside_candidate_count, remaining_target_size)
    return total


def estimate_coverage_entries(n: int, k: int, j: int, s: int) -> int:
    """Estimate how many candidate-target links the full coverage map stores."""
    candidate_count = math.comb(n, k)
    return candidate_count * _calculate_expected_coverage_count(n, k, j, s)


def solve(
    samples: Sequence[int],
    k: int,
    j: int,
    s: int,
    runs: int = 1,
    randomized: bool = False,
) -> Tuple[List[Candidate], Dict[str, object]]:
    """Run the complete solve flow.

    The problem is a set-cover problem: all j-combinations are targets that
    must be covered, and each candidate k-combination covers a subset of those
    targets according to len(J ∩ K) >= s. Greedy set cover repeatedly selects
    the candidate covering the most currently uncovered targets, then redundant
    selected groups are removed by local optimization.
    """
    if isinstance(runs, bool) or not isinstance(runs, int) or runs <= 0:
        raise ValueError("runs must be a positive integer.")

    started_at = time.perf_counter()
    candidates = generate_combinations(samples, k)
    targets = generate_combinations(samples, j)
    coverage_map = build_coverage_map(candidates, targets, s)

    best_result = None
    best_raw_count: Optional[int] = None
    run_summaries = []
    total_runs = runs if randomized else 1

    for run_index in range(1, total_runs + 1):
        raw_result = greedy_set_cover(
            candidates,
            targets,
            coverage_map,
            randomized=randomized,
            top_n=DEFAULT_TOP_N,
        )
        optimized_result = optimize_by_removing_redundant_groups(raw_result, targets, s)

        if not check_all_targets_covered(optimized_result, targets, s):
            raise RuntimeError("Internal error: optimized result does not cover all targets.")

        run_summary = {
            "run": run_index,
            "raw_result_count": len(raw_result),
            "optimized_result_count": len(optimized_result),
        }
        run_summaries.append(run_summary)

        if best_result is None or len(optimized_result) < len(best_result):
            best_result = optimized_result
            best_raw_count = len(raw_result)
        elif len(optimized_result) == len(best_result) and optimized_result < best_result:
            best_result = optimized_result
            best_raw_count = len(raw_result)

    elapsed_seconds = time.perf_counter() - started_at
    final_result = best_result if best_result is not None else []
    stats = {
        "candidate_count": len(candidates),
        "target_count": len(targets),
        "raw_result_count": best_raw_count if best_raw_count is not None else 0,
        "final_result_count": len(final_result),
        "elapsed_seconds": elapsed_seconds,
        "runs": total_runs,
        "randomized": randomized,
        "algorithm": "Greedy Set Cover + Redundant Removal",
        "run_summaries": run_summaries,
        "estimated_coverage_entries": estimate_coverage_entries(len(samples), k, j, s),
    }
    return final_result, stats
