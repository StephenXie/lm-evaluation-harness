# Tower of Hanoi Benchmark

## Overview
Tower of Hanoi evaluates sequential reasoning and planning. Each instance starts with all disks stacked on peg 0 and asks models to output the full move list that transfers the stack to peg 2 while respecting classic constraints (one disk at a time, only top disk moves, never place a larger disk on a smaller one).

## Structure
- `tower_of_hanoi_{3,4,5}.yaml`: Dataset-backed tasks for N=3,4,5 disks (optimal moves: 7/15/31).
- `_default_template.yaml`: Shared configuration (prompt hooks, filters, metrics).
- `_group.yaml`: Convenience group `tower_of_hanoi` aggregating all variants.
- `simulator.py`: Stateful validator enforcing peg bounds, top-disk access, and size ordering.
- `utils.py`: Prompt generation, move extraction, result processing, and custom metrics.
- `dataset_generator.py` (via `scripts/generate_tower_of_hanoi.py`): Reproducible dataset creation.

## Dataset
Generated via `python -m scripts.generate_tower_of_hanoi --disk-counts 3 4 5 --samples-per-count 25 --push`, which pushes splits `N3/N4/N5` to HuggingFace at `Stephen-Xie/TowerOfHanoi`. Each record stores `problem_id`, `num_disks`, initial/goal states, and the canonical optimal move trace.

## Prompt + Output
The prompt concatenates a detailed system description (rules, example) with the instance configuration. Models must respond with `moves = [[disk, from, to], ...]`. A custom filter extracts move lists from generated text before validation.

## Metrics
- `hanoi_solution_valid`: 1 iff every move is legal and the goal state is reached.
- `hanoi_goal_reached`: Goal-only success rate.
- `hanoi_move_accuracy`: Fraction of valid moves per attempt.
- `hanoi_first_error_step`: Index of the first invalid move (-1 if flawless).
- `hanoi_num_moves`: Total moves produced (for monitoring; lower preferred).

## Testing
See `tests/test_tower_of_hanoi.py` for coverage of simulator logic, parser robustness, and end-to-end result processing.

