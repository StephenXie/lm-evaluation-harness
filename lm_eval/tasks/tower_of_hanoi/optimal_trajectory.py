"""
Optimal trajectory generator for Tower of Hanoi problems.

This module provides algorithms to compute optimal move sequences for:
1. Classic Tower of Hanoi (all disks start on one peg, move to another)
2. Arbitrary initial/goal states
"""

from __future__ import annotations

from typing import List, Tuple, Sequence

from lm_eval.tasks.tower_of_hanoi.simulator import HanoiSolutionValidator


# Type aliases
State = Tuple[Tuple[int, ...], ...]  # Immutable state representation
Move = Tuple[int, int, int]  # (disk, from_peg, to_peg)


def _state_to_tuple(state: Sequence[Sequence[int]]) -> State:
    """Convert mutable state to hashable tuple representation."""
    return tuple(tuple(peg) for peg in state)


def _tuple_to_list(state: State) -> List[List[int]]:
    """Convert tuple state back to mutable list representation."""
    return [list(peg) for peg in state]


def _get_disk_position(state: State, disk: int) -> int:
    """Find which peg contains the given disk."""
    for peg_idx, peg in enumerate(state):
        if disk in peg:
            return peg_idx
    raise ValueError(f"Disk {disk} not found in state")


def _can_move(state: State, disk: int, from_peg: int, to_peg: int) -> bool:
    """Check if a move is legal in the given state."""
    if from_peg < 0 or from_peg >= len(state):
        return False
    if to_peg < 0 or to_peg >= len(state):
        return False
    if from_peg == to_peg:
        return False
    
    source = state[from_peg]
    if not source or source[-1] != disk:
        return False
    
    dest = state[to_peg]
    if dest and dest[-1] < disk:
        return False
    
    return True


def _apply_move(state: State, disk: int, from_peg: int, to_peg: int) -> State:
    """Apply a move and return the new state."""
    new_state = _tuple_to_list(state)
    new_state[from_peg] = list(new_state[from_peg])
    new_state[to_peg] = list(new_state[to_peg])
    
    new_state[from_peg] = new_state[from_peg][:-1]
    new_state[to_peg] = new_state[to_peg] + [disk]
    
    return _state_to_tuple(new_state)


def hanoi_with_state(
    num_disks: int,
    initial_state: Sequence[Sequence[int]],
    goal_state: Sequence[Sequence[int]],
    num_pegs: int = 3
) -> List[Move]:
    """
    Find optimal moves for arbitrary Tower of Hanoi initial and goal states.
    
    Uses BFS to find the shortest path from initial to goal state.
    For classic configurations, this will match the recursive algorithm.
    
    Args:
        num_disks: Total number of disks
        initial_state: Starting configuration
        goal_state: Target configuration
        num_pegs: Number of pegs (default 3)
    
    Returns:
        List of moves in format (disk, from_peg, to_peg)
    """
    start = _state_to_tuple(initial_state)
    goal = _state_to_tuple(goal_state)
    
    if start == goal:
        return []
    
    # BFS with state tracking
    queue = [(start, [])]
    visited = {start}
    
    while queue:
        current_state, path = queue.pop(0)
        
        # Try all possible moves
        for peg_idx, peg in enumerate(current_state):
            if not peg:
                continue
            
            disk = peg[-1]  # Top disk
            
            # Try moving to each other peg
            for target_peg in range(num_pegs):
                if target_peg == peg_idx:
                    continue
                
                if _can_move(current_state, disk, peg_idx, target_peg):
                    new_state = _apply_move(current_state, disk, peg_idx, target_peg)
                    
                    if new_state == goal:
                        return path + [(disk, peg_idx, target_peg)]
                    
                    if new_state not in visited:
                        visited.add(new_state)
                        queue.append((new_state, path + [(disk, peg_idx, target_peg)]))
    
    # No solution found
    raise ValueError("No valid solution path found between initial and goal states")


def _resolve_states(
    num_disks: int,
    num_pegs: int,
    initial_state: Sequence[Sequence[int]] | None,
    goal_state: Sequence[Sequence[int]] | None,
) -> tuple[list[list[int]], list[list[int]]]:
    if initial_state is None:
        resolved_initial = [list(range(num_disks, 0, -1))] + [[] for _ in range(num_pegs - 1)]
    else:
        resolved_initial = [list(peg) for peg in initial_state]

    if goal_state is None:
        resolved_goal = [[] for _ in range(num_pegs - 1)] + [list(range(num_disks, 0, -1))]
    else:
        resolved_goal = [list(peg) for peg in goal_state]

    return resolved_initial, resolved_goal


def hanoi_optimal(
    num_disks: int,
    initial_state: Sequence[Sequence[int]] | None = None,
    goal_state: Sequence[Sequence[int]] | None = None,
    num_pegs: int = 3,
) -> List[Move]:
    """
    Generate optimal move sequence for Tower of Hanoi.
    
    This is the main entry point that handles both classic and arbitrary configurations.
    
    Args:
        num_disks: Number of disks
        initial_state: Starting state (if None, all disks on first peg)
        goal_state: Goal state (if None, all disks on last peg)
        num_pegs: Number of pegs (default 3)
    
    Returns:
        List of moves as tuples (disk, from_peg, to_peg)
    """
    resolved_initial, resolved_goal = _resolve_states(num_disks, num_pegs, initial_state, goal_state)
    return hanoi_with_state(num_disks, resolved_initial, resolved_goal, num_pegs)


def format_moves_for_output(moves: List[Move]) -> str:
    """Format moves as a string suitable for output."""
    return "moves = " + str([[disk, from_peg, to_peg] for disk, from_peg, to_peg in moves])


def print_solution(
    num_disks: int,
    initial_state: Sequence[Sequence[int]] | None = None,
    goal_state: Sequence[Sequence[int]] | None = None,
    num_pegs: int = 3,
) -> None:
    """
    Generate and print the optimal solution.
    
    Args:
        num_disks: Number of disks
        initial_state: Starting state
        goal_state: Goal state
        num_pegs: Number of pegs
    """
    resolved_initial, resolved_goal = _resolve_states(num_disks, num_pegs, initial_state, goal_state)
    moves = hanoi_with_state(num_disks, resolved_initial, resolved_goal, num_pegs)
    
    print(f"Optimal solution for {num_disks} disks:")
    print(f"Initial state: {resolved_initial}")
    print(f"Goal state: {resolved_goal}")
    print(f"Number of moves: {len(moves)}")
    print()
    print(format_moves_for_output(moves))
    print()
    
    # Print move-by-move trace
    print("Move sequence:")
    for i, (disk, from_peg, to_peg) in enumerate(moves, 1):
        print(f"  {i}. Move disk {disk} from peg {from_peg} to peg {to_peg}")

    validator = HanoiSolutionValidator()
    summary = validator.validate_solution(
        num_disks=num_disks,
        moves=moves,
        num_pegs=num_pegs,
        initial_state=resolved_initial,
        goal_state=resolved_goal,
    )

    if summary.is_valid:
        print("Validator: solution is valid and reaches the goal state.")
    else:
        print("Validator: solution is INVALID.")
        if summary.error_messages:
            print("  Errors:")
            for message in summary.error_messages:
                print(f"    - {message}")
        if not summary.goal_reached:
            print("  Goal state was not reached.")


if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python optimal_trajectory.py <num_disks>")
        print("  python optimal_trajectory.py <num_disks> <source_peg> <target_peg>")
        print("  python optimal_trajectory.py --json '<json_problem>'")
        print()
        print("Examples:")
        print("  python optimal_trajectory.py 3")
        print("  python optimal_trajectory.py 4 0 2")
        print('  python optimal_trajectory.py --json \'{"num_disks": 3, "initial_state": [[3,2,1],[],[]], "goal_state": [[],[],[3,2,1]]}\'')
        sys.exit(1)
    
    if sys.argv[1] == "--json":
        # Parse JSON problem
        problem = json.loads(sys.argv[2])
        num_disks = problem["num_disks"]
        initial_state = problem.get("initial_state")
        goal_state = problem.get("goal_state")
        num_pegs = problem.get("num_pegs", 3)
        
        print_solution(num_disks, initial_state, goal_state, num_pegs)
    else:
        # Parse simple arguments
        num_disks = int(sys.argv[1])
        
        if len(sys.argv) >= 4:
            source = int(sys.argv[2])
            target = int(sys.argv[3])
            num_pegs = int(sys.argv[4]) if len(sys.argv) > 4 else 3
            
            initial_state = [[] for _ in range(num_pegs)]
            initial_state[source] = list(range(num_disks, 0, -1))
            
            goal_state = [[] for _ in range(num_pegs)]
            goal_state[target] = list(range(num_disks, 0, -1))
            
            print_solution(num_disks, initial_state, goal_state, num_pegs)
        else:
            print_solution(num_disks)

