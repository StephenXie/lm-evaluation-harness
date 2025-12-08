"""Tower of Hanoi simulator and validator utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence


def _clone_state(state: Sequence[Sequence[int]]) -> List[List[int]]:
    return [list(peg) for peg in state]


@dataclass
class MoveValidationResult:
    is_valid: bool
    message: str | None = None


class TowerOfHanoiState:
    """Mutable Tower of Hanoi puzzle state."""

    def __init__(
        self,
        num_disks: int,
        num_pegs: int = 3,
        initial_state: Sequence[Sequence[int]] | None = None,
    ) -> None:
        if num_disks <= 0:
            raise ValueError("TowerOfHanoiState requires at least one disk.")
        if num_pegs < 3:
            raise ValueError("TowerOfHanoiState requires at least three pegs.")
        self.num_disks = num_disks
        self.num_pegs = num_pegs
        # Default: all disks on first peg, rest empty
        default_state = [list(range(num_disks, 0, -1))] + [[] for _ in range(num_pegs - 1)]
        self.pegs = _clone_state(initial_state) if initial_state else default_state
        if len(self.pegs) != num_pegs:
            raise ValueError(f"Initial state must contain exactly {num_pegs} pegs.")
        self.move_count = 0

    def get_state(self) -> List[List[int]]:
        """Return a deepcopy of the peg configuration."""
        return _clone_state(self.pegs)

    def is_valid_move(self, disk: int, from_peg: int, to_peg: int) -> MoveValidationResult:
        """Check whether a move obeys Hanoi constraints."""
        if not (0 <= from_peg < self.num_pegs) or not (0 <= to_peg < self.num_pegs):
            return MoveValidationResult(False, f"Peg index must be between 0 and {self.num_pegs - 1}.")
        if from_peg == to_peg:
            return MoveValidationResult(False, "Source and target peg must differ.")
        source = self.pegs[from_peg]
        if not source:
            return MoveValidationResult(False, f"Peg {from_peg} has no disks to move.")
        top_disk = source[-1]
        if top_disk != disk:
            return MoveValidationResult(
                False,
                f"Disk {disk} is not on top of peg {from_peg} (found disk {top_disk}).",
            )
        dest = self.pegs[to_peg]
        if dest and dest[-1] < disk:
            return MoveValidationResult(
                False,
                f"Cannot place disk {disk} on smaller disk {dest[-1]} (peg {to_peg}).",
            )
        return MoveValidationResult(True)

    def execute_move(self, disk: int, from_peg: int, to_peg: int) -> MoveValidationResult:
        """Validate and apply a move, returning the validation result."""
        validation = self.is_valid_move(disk, from_peg, to_peg)
        if not validation.is_valid:
            return validation
        moving_disk = self.pegs[from_peg].pop()
        self.pegs[to_peg].append(moving_disk)
        self.move_count += 1
        return MoveValidationResult(True)

    def is_goal_reached(self, goal_state: Sequence[Sequence[int]] | None = None) -> bool:
        """Check whether the puzzle matches the desired terminal configuration."""
        if goal_state:
            target = _clone_state(goal_state)
        else:
            # Default: all disks on last peg, rest empty
            target = [[] for _ in range(self.num_pegs - 1)] + [list(range(self.num_disks, 0, -1))]
        return self.get_state() == target


@dataclass
class ValidationSummary:
    is_valid: bool
    goal_reached: bool
    num_valid_moves: int
    total_moves: int
    first_error_index: int | None
    error_messages: list[str] = field(default_factory=list)
    final_state: list[list[int]] | None = None
    has_malformed_moves: bool = False  # True if moves have wrong format (vs just illegal)


class HanoiSolutionValidator:
    """Validates entire Tower of Hanoi solution traces."""

    def validate_solution(
        self,
        num_disks: int,
        moves: Sequence[Sequence[int]] | None,
        num_pegs: int = 3,
        initial_state: Sequence[Sequence[int]] | None = None,
        goal_state: Sequence[Sequence[int]] | None = None,
    ) -> ValidationSummary:
        state = TowerOfHanoiState(num_disks, num_pegs, initial_state)
        error_messages: list[str] = []
        num_valid_moves = 0
        first_error_index: int | None = None
        has_malformed_moves = False

        if moves is None:
            error_messages.append("No moves provided.")
            has_malformed_moves = True
            return ValidationSummary(
                is_valid=False,
                goal_reached=False,
                num_valid_moves=0,
                total_moves=0,
                first_error_index=None,
                error_messages=error_messages,
                final_state=state.get_state(),
                has_malformed_moves=has_malformed_moves,
            )

        for idx, raw_move in enumerate(moves):
            if (
                not isinstance(raw_move, (list, tuple))
                or len(raw_move) != 3
                or not all(isinstance(x, int) for x in raw_move)
            ):
                first_error_index = idx
                error_messages.append(f"Malformed move at index {idx}: {raw_move}")
                has_malformed_moves = True
                break

            disk, from_peg, to_peg = raw_move
            outcome = state.execute_move(disk, from_peg, to_peg)
            if not outcome.is_valid:
                first_error_index = idx
                error_messages.append(outcome.message or "Invalid move.")
                # Not malformed, just illegal - don't set has_malformed_moves
                break
            num_valid_moves += 1

        goal_reached = state.is_goal_reached(goal_state)
        is_valid = goal_reached and first_error_index is None

        return ValidationSummary(
            is_valid=is_valid,
            goal_reached=goal_reached,
            num_valid_moves=num_valid_moves,
            total_moves=len(moves),
            first_error_index=first_error_index,
            error_messages=error_messages,
            final_state=state.get_state(),
            has_malformed_moves=has_malformed_moves,
        )

