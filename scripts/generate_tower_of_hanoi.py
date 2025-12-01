"""
Utility script to generate Tower of Hanoi datasets and optionally push them to
the Hugging Face Hub.

Usage examples:

    # Generate JSONL files only (defaults to N=3,4,5, 3 pegs, and 25 samples each)
    python scripts/generate_tower_of_hanoi.py

    # Generate 50 samples each for disk counts 3 and 5, save elsewhere
    python scripts/generate_tower_of_hanoi.py \
        --disk-counts 3 5 \
        --samples-per-count 50 \
        --output-dir /tmp/hanoi_data

    # Generate with 4 pegs instead of default 3
    python scripts/generate_tower_of_hanoi.py --num-pegs 4

    # Generate data and push every split to hf.co/Stephen-Xie/TowerOfHanoi
    python scripts/generate_tower_of_hanoi.py --push
"""

from __future__ import annotations

import argparse
import json
import math
import random
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
        "--num-pegs",
        type=int,
        default=3,
        help="Number of pegs in the Tower of Hanoi puzzle (default: 3).",
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


def generate_random_legal_state(num_disks: int, num_pegs: int, rng: random.Random) -> List[List[int]]:
    """Generate a random legal Tower of Hanoi state with disks distributed across pegs."""
    # Create list of all disks
    disks = list(range(1, num_disks + 1))
    
    # Initialize pegs
    state = [[] for _ in range(num_pegs)]
    
    # Randomly assign each disk to a peg
    for disk in disks:
        peg = rng.randint(0, num_pegs - 1)
        state[peg].append(disk)
    
    # Sort each peg so larger disks are at the bottom (valid Tower of Hanoi configuration)
    for peg in state:
        peg.sort(reverse=True)
    
    return state


def states_are_equal(state1: List[List[int]], state2: List[List[int]]) -> bool:
    """Check if two Tower of Hanoi states are identical."""
    return all(peg1 == peg2 for peg1, peg2 in zip(state1, state2))


def build_examples(num_disks: int, num_pegs: int, samples: int) -> list[dict]:
    """Create varied problem instances with random legal initial and goal states."""
    # Use a seeded RNG for reproducibility
    rng = random.Random(42)
    
    records = []
    for idx in range(1, samples + 1):
        # Generate random initial state
        initial_state = generate_random_legal_state(num_disks, num_pegs, rng)
        
        # Generate random goal state that's different from initial
        goal_state = generate_random_legal_state(num_disks, num_pegs, rng)
        while states_are_equal(initial_state, goal_state):
            goal_state = generate_random_legal_state(num_disks, num_pegs, rng)
        
        # Note: We don't compute solution_moves for arbitrary states as it's complex
        # The evaluation harness will need to determine if the model's solution is valid
        # For now, we'll set these to None or placeholder values
        records.append(
            {
                "problem_id": f"hanoi_{num_disks}_p{num_pegs}_{idx:03d}",
                "num_disks": num_disks,
                "num_pegs": num_pegs,
                "initial_state": initial_state,
                "goal_state": goal_state,
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
    
    if args.num_pegs < 3:
        raise ValueError(f"Number of pegs must be at least 3: got {args.num_pegs}")

    for num_disks in args.disk_counts:
        docs = build_examples(num_disks, args.num_pegs, args.samples_per_count)
        jsonl_path = args.output_dir / f"hanoi_{num_disks}_p{args.num_pegs}.jsonl"
        write_jsonl(jsonl_path, docs)
        print(f"Wrote {len(docs)} samples for N={num_disks}, P={args.num_pegs} -> {jsonl_path}")

        if args.push:
            config_name = f"N{num_disks}_P{args.num_pegs}"
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

