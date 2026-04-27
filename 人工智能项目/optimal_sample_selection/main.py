"""Command line interface for An Optimal Samples Selection System."""

import math
import sys
from typing import List, Tuple

from optimal_sample_selection.solver import estimate_coverage_entries, solve
from optimal_sample_selection.storage import (
    delete_result_file,
    display_result_file,
    list_result_files,
    save_result,
)
from optimal_sample_selection.utils import (
    LARGE_COMBINATION_WARNING_THRESHOLD,
    choose_samples_randomly,
    parse_user_samples,
    read_positive_integer,
    read_yes_no,
    validate_parameters,
)


TITLE = "An Optimal Samples Selection System"
MENU_TEXT = """
========================================
An Optimal Samples Selection System
========================================
1. Execute / Run new selection
2. List saved result files
3. Display a saved result file
4. Delete a saved result file
5. Exit
""".strip()


def _print_title() -> None:
    print("=" * 40)
    print(TITLE)
    print("=" * 40)


def _read_parameters() -> Tuple[int, int, int, int, int]:
    while True:
        m = read_positive_integer("m: ")
        n = read_positive_integer("n: ")
        k = read_positive_integer("k: ")
        j = read_positive_integer("j: ")
        s = read_positive_integer("s: ")

        try:
            validate_parameters(m, n, k, j, s)
            return m, n, k, j, s
        except ValueError as error:
            print(f"Parameter error: {error}")
            print("Please enter the parameters again.\n")


def _read_samples(m: int, n: int) -> List[int]:
    while True:
        print("Select sample input mode:")
        print("1. Random n samples")
        print("2. Manual input n samples")
        mode = input("Please select an option: ").strip()

        if mode == "1":
            return choose_samples_randomly(m, n)
        if mode == "2":
            raw_samples = input(f"Enter {n} sample numbers separated by spaces: ")
            try:
                return parse_user_samples(raw_samples, m, n)
            except ValueError as error:
                print(f"Sample input error: {error}")
                print("Please choose the sample input mode again.\n")
        else:
            print("Invalid option. Please select 1 or 2.")


def _confirm_large_problem(n: int, k: int, j: int, s: int) -> bool:
    candidate_count = math.comb(n, k)
    target_count = math.comb(n, j)
    estimated_entries = estimate_coverage_entries(n, k, j, s)

    print(f"Candidate k-combination count: {candidate_count}")
    print(f"Target j-combination count: {target_count}")
    print(f"Estimated coverage links: {estimated_entries}")

    if candidate_count > LARGE_COMBINATION_WARNING_THRESHOLD:
        print("Warning: candidate combination count is large and may run slowly.")
        return read_yes_no("Continue anyway?", default=False)
    if target_count > LARGE_COMBINATION_WARNING_THRESHOLD:
        print("Warning: target combination count is large and may run slowly.")
        return read_yes_no("Continue anyway?", default=False)
    if estimated_entries > LARGE_COMBINATION_WARNING_THRESHOLD * 20:
        print("Warning: coverage map may require significant memory/time.")
        return read_yes_no("Continue anyway?", default=False)

    return True


def _read_randomized_options() -> Tuple[bool, int]:
    randomized = read_yes_no("Enable randomized greedy?", default=False)
    if not randomized:
        return False, 1

    runs = read_positive_integer("Enter number of runs: ")
    return True, runs


def _print_run_summary(
    m: int,
    n: int,
    k: int,
    j: int,
    s: int,
    samples: List[int],
    results: List[Tuple[int, ...]],
    stats: dict,
    file_path: str,
) -> None:
    _print_title()
    print("Input Parameters")
    print(f"m={m}")
    print(f"n={n}")
    print(f"k={k}")
    print(f"j={j}")
    print(f"s={s}")
    print("Selected Samples")
    print(" ".join(str(sample) for sample in samples))
    print("Algorithm Statistics")
    print(f"Candidate k-combination count: {stats['candidate_count']}")
    print(f"Target j-combination count: {stats['target_count']}")
    print(f"Greedy raw result count: {stats['raw_result_count']}")
    print(f"Final result count after redundant removal: {stats['final_result_count']}")
    print(f"Runs: {stats['runs']}")
    print(f"Randomized greedy: {stats['randomized']}")
    print(f"Running time: {stats['elapsed_seconds']:.4f} seconds")
    print("Final Result Groups")
    for index, group in enumerate(results, start=1):
        print(f"{index}: " + " ".join(str(value) for value in group))
    print(f"Saved file path: {file_path}")


def run_new_selection() -> None:
    _print_title()
    m, n, k, j, s = _read_parameters()
    samples = _read_samples(m, n)

    print("Current selected samples:")
    print(" ".join(str(sample) for sample in samples))

    if not _confirm_large_problem(n, k, j, s):
        print("Run cancelled by user.")
        return

    randomized, runs = _read_randomized_options()

    try:
        results, stats = solve(samples, k, j, s, runs=runs, randomized=randomized)
        file_path = save_result(m, n, k, j, s, samples, results, stats)
        _print_run_summary(m, n, k, j, s, samples, results, stats, file_path)
    except (RuntimeError, ValueError, OSError) as error:
        print(f"Execution failed: {error}")


def _select_file() -> str:
    filenames = list_result_files()
    if not filenames:
        print("No saved result files found.")
        return ""

    for index, filename in enumerate(filenames, start=1):
        print(f"{index}. {filename}")

    while True:
        selected_index = read_positive_integer("Please select a file number: ")
        if 1 <= selected_index <= len(filenames):
            return filenames[selected_index - 1]
        print("Invalid file number. Please try again.")


def list_saved_files() -> None:
    filenames = list_result_files()
    if not filenames:
        print("No saved result files found.")
        return

    print("Saved result files:")
    for index, filename in enumerate(filenames, start=1):
        print(f"{index}. {filename}")


def display_saved_file() -> None:
    filename = _select_file()
    if not filename:
        return

    try:
        content = display_result_file(filename)
        print("-" * 40)
        print(content.rstrip())
        print("-" * 40)
    except (OSError, ValueError) as error:
        print(f"Failed to display file: {error}")


def delete_saved_file() -> None:
    filename = _select_file()
    if not filename:
        return

    if not read_yes_no(f"Delete {filename}?", default=False):
        print("Delete cancelled.")
        return

    try:
        delete_result_file(filename)
        print("File deleted successfully.")
    except (OSError, ValueError) as error:
        print(f"Failed to delete file: {error}")


def main() -> None:
    while True:
        print(MENU_TEXT)
        choice = input("Please select an option: ").strip()

        if choice == "1":
            run_new_selection()
        elif choice == "2":
            list_saved_files()
        elif choice == "3":
            display_saved_file()
        elif choice == "4":
            delete_saved_file()
        elif choice == "5":
            print("Goodbye.")
            break
        else:
            print("Invalid option. Please select 1, 2, 3, 4, or 5.")

        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(1)
