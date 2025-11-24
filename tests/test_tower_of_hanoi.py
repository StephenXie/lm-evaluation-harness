from __future__ import annotations

import pytest

from lm_eval.tasks.tower_of_hanoi import simulator, utils


def _hanoi_solution(n: int, start: int = 0, target: int = 2, aux: int = 1):
    moves: list[list[int]] = []

    def _solve(k: int, src: int, dst: int, spare: int):
        if k == 0:
            return
        _solve(k - 1, src, spare, dst)
        moves.append([k, src, dst])
        _solve(k - 1, spare, dst, src)

    _solve(n, start, target, aux)
    return moves


def _doc(num_disks: int = 3):
    return {
        "num_disks": num_disks,
        "initial_state": [list(range(num_disks, 0, -1)), [], []],
        "goal_state": [[], [], list(range(num_disks, 0, -1))],
    }


def test_state_executes_optimal_sequence():
    moves = _hanoi_solution(3)
    state = simulator.TowerOfHanoiState(3)

    for disk, src, dst in moves:
        result = state.execute_move(disk, src, dst)
        assert result.is_valid, result.message

    assert state.is_goal_reached()
    assert state.move_count == len(moves)


def test_state_rejects_illegal_move():
    state = simulator.TowerOfHanoiState(3)
    invalid = state.execute_move(2, 0, 1)  # disk 2 not on top initially
    assert not invalid.is_valid
    assert "Disk 2 is not on top" in invalid.message


def test_validator_detects_goal_and_errors():
    validator = simulator.HanoiSolutionValidator()
    valid = validator.validate_solution(3, _hanoi_solution(3))
    assert valid.is_valid
    assert valid.goal_reached
    assert valid.first_error_index is None

    invalid = validator.validate_solution(3, [[3, 0, 2]])
    assert not invalid.is_valid
    assert not invalid.goal_reached
    assert invalid.first_error_index == 0


def test_extract_moves_from_response_parses_list():
    resp = ["Final answer:\nmoves = [[1, 0, 2], [2, 0, 1], [1, 2, 1]]"]
    parsed = utils.extract_moves_from_response([resp], [{}])
    payload = parsed[0][0]
    assert payload["moves"] == [[1, 0, 2], [2, 0, 1], [1, 2, 1]]
    assert payload["parse_error"] is None


def test_process_results_successful_solution():
    doc = _doc()
    metrics = utils.process_results(doc, [[{"moves": _hanoi_solution(3)}]])
    assert metrics["hanoi_solution_valid"] == 1.0
    assert metrics["hanoi_goal_reached"] == 1.0
    assert metrics["hanoi_move_accuracy"] == pytest.approx(1.0)


def test_process_results_handles_parse_failures():
    doc = _doc()
    payload = {"moves": None, "parse_error": "bad format"}
    metrics = utils.process_results(doc, [[payload]])
    assert metrics["hanoi_solution_valid"] == 0.0
    assert metrics["hanoi_goal_reached"] == 0.0
    assert metrics["hanoi_move_accuracy"] == 0.0

