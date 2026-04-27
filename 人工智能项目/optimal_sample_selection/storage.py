"""Result file storage helpers."""

import os
from datetime import datetime
from typing import Dict, List, Sequence, Tuple


DATA_DIR = os.path.abspath(os.path.join(os.getcwd(), "data"))


def _ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def _validate_result_filename(filename: str) -> str:
    basename = os.path.basename(filename)
    if basename != filename:
        raise ValueError("Only files inside the data directory can be accessed.")
    if not basename.endswith(".txt"):
        raise ValueError("Only .txt result files can be accessed.")

    full_path = os.path.abspath(os.path.join(DATA_DIR, basename))
    data_root = os.path.abspath(DATA_DIR)
    if os.path.commonpath([data_root, full_path]) != data_root:
        raise ValueError("Invalid result file path.")
    return full_path


def _next_save_index(m: int, n: int, k: int, j: int, s: int) -> int:
    _ensure_data_dir()
    prefix = f"{m}-{n}-{k}-{j}-{s}-"
    max_index = 0

    for filename in os.listdir(DATA_DIR):
        if not filename.startswith(prefix) or not filename.endswith(".txt"):
            continue
        name_without_extension = filename[:-4]
        parts = name_without_extension.split("-")
        if len(parts) != 7:
            continue
        try:
            save_index = int(parts[5])
        except ValueError:
            continue
        if save_index > max_index:
            max_index = save_index

    return max_index + 1


def save_result(
    m: int,
    n: int,
    k: int,
    j: int,
    s: int,
    samples: Sequence[int],
    results: Sequence[Tuple[int, ...]],
    stats: Dict[str, object],
) -> str:
    """Save a solve result to the data directory and return the file path."""
    _ensure_data_dir()
    save_index = _next_save_index(m, n, k, j, s)
    result_count = len(results)
    filename = f"{m}-{n}-{k}-{j}-{s}-{save_index}-{result_count}.txt"
    file_path = os.path.join(DATA_DIR, filename)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    algorithm = str(stats.get("algorithm", "Greedy Set Cover + Redundant Removal"))

    lines = [
        "Parameters",
        f"m={m}",
        f"n={n}",
        f"k={k}",
        f"j={j}",
        f"s={s}",
        "selected_samples=" + " ".join(str(sample) for sample in samples),
        f"result_count={result_count}",
        f"created_at={created_at}",
        f"algorithm={algorithm}",
        "",
        "Results",
    ]

    for index, group in enumerate(results, start=1):
        lines.append(f"{index}: " + " ".join(str(value) for value in group))

    with open(file_path, "w", encoding="utf-8") as file_object:
        file_object.write("\n".join(lines) + "\n")

    return file_path


def list_result_files() -> List[str]:
    """List saved .txt result files in the data directory."""
    _ensure_data_dir()
    filenames = []
    for filename in os.listdir(DATA_DIR):
        full_path = os.path.join(DATA_DIR, filename)
        if os.path.isfile(full_path) and filename.endswith(".txt"):
            filenames.append(filename)
    return sorted(filenames)


def display_result_file(filename: str) -> str:
    """Read and return the content of a saved result file."""
    file_path = _validate_result_filename(filename)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Result file not found: {filename}")

    with open(file_path, "r", encoding="utf-8") as file_object:
        return file_object.read()


def delete_result_file(filename: str) -> None:
    """Delete a saved result file from the data directory."""
    file_path = _validate_result_filename(filename)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Result file not found: {filename}")
    os.remove(file_path)
