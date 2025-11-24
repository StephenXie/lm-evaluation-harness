"""
Utility script to generate Tower of Hanoi datasets and optionally push them to
the Hugging Face Hub.

Usage examples:

    # Generate JSONL files only (defaults to N=3,4,5 and 25 samples each)
    python scripts/generate_tower_of_hanoi.py

    # Generate 50 samples each for disk counts 3 and 5, save elsewhere
    python scripts/generate_tower_of_hanoi.py \
        --disk-counts 3 5 \
        --samples-per-count 50 \
        --output-dir /tmp/hanoi_data

    # Generate data and push every split to hf.co/Stephen-Xie/TowerOfHanoi
    python scripts/generate_tower_of_hanoi.py --push
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable, List, Sequence

from datasets import Dataset, DatasetDict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--disk-counts",
        type=int,
        nargs="+",
        default=[3, 4, 5],
        help="Which disk counts to generate (default: 3 4 5).",
    )
    parser.add_argument(
        "--samples-per-count",
        type=int,
        default=25,
        help="How many identical problem instances to clone per disk count.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("lm_eval/tasks/tower_of_hanoi/data"),
        help="Where to write JSONL files.",
    )
    parser.add_argument(
        "--repo-id",
        type=str,
        default="Stephen-Xie/TowerOfHanoi",
        help="Target dataset repository on the Hugging Face Hub.",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="If set, push each disk-count split to the HF Hub. "
        "Requires HF auth (huggingface-cli login).",
    )
    return parser.parse_args()


def generate_moves(n: int, start: int = 0, target: int = 2, aux: int = 1) -> List[List[int]]:
    """Classic recursive Tower of Hanoi solver returning [disk, from, to] moves."""

    def _solve(num: int, src: int, dst: int, spare: int, acc: List[List[int]]) -> None:
        if num == 0:
            return
        _solve(num - 1, src, spare, dst, acc)
        acc.append([num, src, dst])
        _solve(num - 1, spare, dst, src, acc)

    moves: List[List[int]] = []
    _solve(n, start, target, aux, moves)
    return moves


def build_examples(num_disks: int, samples: int) -> list[dict]:
    """Create repeated problem instances for a fixed disk count."""
    base_initial = [list(range(num_disks, 0, -1)), [], []]
    base_goal = [[], [], list(range(num_disks, 0, -1))]
    solution_moves = generate_moves(num_disks)
    optimal_moves = int(math.pow(2, num_disks) - 1)

    records = []
    for idx in range(1, samples + 1):
        records.append(
            {
                "problem_id": f"hanoi_{num_disks}_{idx:03d}",
                "num_disks": num_disks,
                "initial_state": base_initial,
                "goal_state": base_goal,
                "solution_moves": solution_moves,
                "optimal_num_moves": optimal_moves,
            }
        )
    return records


def write_jsonl(path: Path, docs: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc))
            f.write("\n")


def push_dataset(repo_id: str, config_name: str, docs: Sequence[dict]) -> None:
    dataset = Dataset.from_list(list(docs))
    DatasetDict({"test": dataset}).push_to_hub(repo_id, config_name=config_name)


def main() -> None:
    args = parse_args()
    missing = [n for n in args.disk_counts if n <= 0]
    if missing:
        raise ValueError(f"Disk counts must be positive: got {missing}")

    for num_disks in args.disk_counts:
        docs = build_examples(num_disks, args.samples_per_count)
        jsonl_path = args.output_dir / f"hanoi_{num_disks}.jsonl"
        write_jsonl(jsonl_path, docs)
        print(f"Wrote {len(docs)} samples for N={num_disks} -> {jsonl_path}")

        if args.push:
            config_name = f"N{num_disks}"
            push_dataset(args.repo_id, config_name, docs)
            print(f"Pushed {config_name} split to {args.repo_id}")

    if args.push:
        print(
            "Upload complete. Verify on https://huggingface.co/datasets/"
            f"{args.repo_id}"
        )
    else:
        print("Skipping push. Use --push to upload to Hugging Face.")


if __name__ == "__main__":
    main()

