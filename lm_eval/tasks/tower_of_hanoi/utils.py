"""Helper functions for the Tower of Hanoi evaluation task."""

from __future__ import annotations

import ast
import re
from textwrap import dedent
from typing import Any, Iterable

from .simulator import HanoiSolutionValidator

SYSTEM_PROMPT = dedent(
    """\
    You are a helpful assistant. Solve this puzzle for me.

    There are three pegs and n disks of different sizes stacked on the first peg. The disks
    are numbered from 1 (smallest) to n (largest). Disk moves in this puzzle should follow:

    1. Only one disk can be moved at a time.
    2. Each move consists of taking the upper disk from one stack and placing it on top of another stack.
    3. A larger disk may not be placed on top of a smaller disk.

    The goal is to move the entire stack to the third peg.

    Example: With 3 disks numbered 1 (smallest), 2, and 3 (largest), the initial state is [[3, 2, 1], [], []],
    and a solution might be:

    moves = [[1, 0, 2], [2, 0, 1], [1, 2, 1], [3, 0, 2], [1, 1, 0], [2, 1, 2], [1, 0, 2]]

    This means: Move disk 1 from peg 0 to peg 2, then move disk 2 from peg 0 to peg 1, and so on.

    Requirements:
    - When exploring potential solutions in your reasoning, include the complete list of moves.
    - Pegs are 0-indexed (leftmost peg is 0).
    - Ensure the final answer includes the moves in the format: moves = [[disk id, from peg, to peg], ...]
    """
)

VALIDATOR = HanoiSolutionValidator()


# ---------------------------------------------------------------------------
# Prompt construction helpers
# ---------------------------------------------------------------------------
def doc_to_text(doc: dict) -> str:
    return f"{SYSTEM_PROMPT}\n\n{generate_user_prompt(doc)}"


def doc_to_target(doc: dict) -> str:
    # Target is unused because we score by validating the generated solution.
    return " "


def generate_user_prompt(doc: dict) -> str:
    num_disks = doc["num_disks"]
    initial = render_configuration(doc["initial_state"])
    goal = render_configuration(doc["goal_state"])

    return dedent(
        f"""\
        I have a puzzle with {num_disks} disks of different sizes with

        Initial configuration:
        {initial}

        Goal configuration:
        {goal}

        Rules:
        - Only one disk can be moved at a time.
        - Only the top disk from any stack can be moved.
        - A larger disk may not be placed on top of a smaller disk.

        Find the sequence of moves to transform the initial configuration into the goal configuration.
        Remember to output the full move list with 0-indexed pegs using the format moves = [[disk id, from peg, to peg], ...].
        """
    ).strip()


def render_configuration(state: Iterable[Iterable[int]]) -> str:
    lines = []
    for idx, peg in enumerate(state):
        peg_list = list(peg)
        peg_str = ", ".join(str(d) for d in peg_list) if peg_list else "(empty)"
        lines.append(f"- Peg {idx}: {peg_str} (bottom->top)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Response parsing + filtering
# ---------------------------------------------------------------------------
def extract_moves_from_response(resps: list[list[str]], docs: list[dict]) -> list[list[dict]]:
    return [[_parse_response(text) for text in resp_set] for resp_set in resps]


def _parse_response(text: str) -> dict[str, Any]:
    cleaned = _strip_code_fences(text)
    candidate = _find_moves_block(cleaned)
    moves = _literal_eval_moves(candidate) if candidate else None
    error = None
    if moves is None:
        error = "Failed to parse move list."
    return {
        "raw": text,
        "candidate": candidate,
        "moves": moves,
        "parse_error": error,
    }


def _strip_code_fences(text: str) -> str:
    if "```" not in text:
        return text
    blocks = re.findall(r"```(?:\w+)?\s*([\s\S]+?)```", text)
    return "\n\n".join(blocks) if blocks else text


def _find_moves_block(text: str) -> str | None:
    match = re.search(r"moves\s*=", text, re.IGNORECASE)
    search_start = match.end() if match else 0
    start = text.find("[", search_start)
    if start == -1:
        start = text.find("[")
    if start == -1:
        return None

    depth = 0
    end = None
    for idx in range(start, len(text)):
        char = text[idx]
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                end = idx + 1
                break
    return text[start:end] if end else None


def _literal_eval_moves(candidate: str | None) -> list[list[int]] | None:
    if not candidate:
        return None
    try:
        parsed = ast.literal_eval(candidate)
    except (SyntaxError, ValueError):
        return None

    if not isinstance(parsed, (list, tuple)):
        return None

    moves: list[list[int]] = []
    for move in parsed:
        if (
            isinstance(move, (list, tuple))
            and len(move) == 3
            and all(isinstance(x, int) for x in move)
        ):
            moves.append([int(move[0]), int(move[1]), int(move[2])])
        else:
            return None
    return moves


# ---------------------------------------------------------------------------
# Result processing + metrics
# ---------------------------------------------------------------------------
def process_results(doc: dict, results: list) -> dict[str, float]:
    payloads = results[0] if results else []
    payload = payloads[0] if payloads else {}
    moves = payload.get("moves") if isinstance(payload, dict) else None

    summary = VALIDATOR.validate_solution(
        num_disks=doc["num_disks"],
        moves=moves,
        initial_state=doc.get("initial_state"),
        goal_state=doc.get("goal_state"),
    )

    if isinstance(payload, dict) and payload.get("parse_error"):
        summary.error_messages.append(payload["parse_error"])

    move_accuracy = (
        summary.num_valid_moves / summary.total_moves if summary.total_moves else 0.0
    )
    first_error = summary.first_error_index if summary.first_error_index is not None else -1

    return {
        "hanoi_solution_valid": 1.0 if summary.is_valid else 0.0,
        "hanoi_goal_reached": 1.0 if summary.goal_reached else 0.0,
        "hanoi_move_accuracy": move_accuracy,
        "hanoi_first_error_step": float(first_error),
        "hanoi_num_moves": float(summary.total_moves),
    }

