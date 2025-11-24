# Tower of Hanoi Implementation - Quick Reference

## File Structure
```
lm_eval/tasks/tower_of_hanoi/
├── simulator.py              # Core validation logic
├── utils.py                  # Prompt generation, parsing, metrics
├── dataset_generator.py      # Generate problem instances
├── _default_template.yaml    # Shared YAML config
├── tower_of_hanoi_N.yaml    # Task configs (N=3,4,5,6,7)
├── _group.yaml              # Group all variants
├── data/
│   └── hanoi_N.jsonl        # Dataset files
├── README.md                # Documentation
└── __init__.py
```

## Core Classes

### 1. TowerOfHanoiState (simulator.py)
```python
class TowerOfHanoiState:
    def __init__(self, num_disks: int)
    def is_valid_move(self, disk, from_peg, to_peg) -> (bool, str)
    def execute_move(self, disk, from_peg, to_peg) -> bool
    def is_goal_reached() -> bool
```

### 2. HanoiSolutionValidator (simulator.py)
```python
class HanoiSolutionValidator:
    def validate_solution(self, num_disks, moves) -> dict:
        # Returns: is_valid, goal_reached, num_valid_moves, 
        #          first_error_index, error_messages, final_state
```

## Key Functions (utils.py)

| Function | Purpose |
|----------|---------|
| `doc_to_text(doc)` | Generate system + user prompt |
| `doc_to_target(doc)` | Return expected output format |
| `extract_moves_from_response(resps, docs)` | Parse model response to extract moves |
| `process_results(doc, results)` | Validate and compute metrics |
| `hanoi_solution_valid(items)` | Metric: % fully correct solutions |
| `hanoi_goal_reached(items)` | Metric: % reaching goal state |
| `hanoi_move_accuracy(items)` | Metric: avg per-move accuracy |

## Dataset Format
```json
{
    "problem_id": "hanoi_3_001",
    "num_disks": 3,
    "initial_state": [[3, 2, 1], [], []],
    "goal_state": [[], [], [3, 2, 1]],
    "optimal_moves": 7
}
```

## Response Format
```python
moves = [[disk_id, from_peg, to_peg], ...]
# Example: [[1, 0, 2], [2, 0, 1], [1, 2, 1], [3, 0, 2], ...]
```

## Validation Rules (4-Layer)
1. **Peg Boundary**: from_peg, to_peg ∈ {0, 1, 2}
2. **Source Check**: from_peg must contain disks
3. **Top Disk Check**: specified disk must be topmost on from_peg
4. **Size Constraint**: larger disk cannot go on smaller disk

## Metrics

| Metric | Description | Range |
|--------|-------------|-------|
| `hanoi_solution_valid` | Complete valid solution reaching goal | [0, 1] |
| `hanoi_goal_reached` | Reached goal (even if invalid moves) | [0, 1] |
| `hanoi_move_accuracy` | Valid moves / total moves | [0, 1] |
| `hanoi_first_error_step` | Step # of first error (-1 if none) | [-1, ∞) |

## Task Variants

| Task | Disks | Optimal Moves | Difficulty |
|------|-------|---------------|------------|
| `tower_of_hanoi_3` | 3 | 7 | Baseline |
| `tower_of_hanoi_4` | 4 | 15 | Easy |
| `tower_of_hanoi_5` | 5 | 31 | Medium |
| `tower_of_hanoi_6` | 6 | 63 | Hard |
| `tower_of_hanoi_7` | 7 | 127 | Very Hard |
| `tower_of_hanoi` | All | - | Group |

## Implementation Checklist

### Phase 1: Dataset ✓
- [ ] Create `dataset_generator.py`
- [ ] Generate JSONL files for N=3,4,5,6,7
- [ ] Store in `data/` subdirectory

### Phase 2: Simulator ✓
- [ ] Implement `TowerOfHanoiState` class
- [ ] Implement 4-layer validation
- [ ] Implement `HanoiSolutionValidator`
- [ ] Write unit tests

### Phase 3: Configuration ✓
- [ ] Create `_default_template.yaml`
- [ ] Create individual task YAMLs (N=3-7)
- [ ] Create `_group.yaml`

### Phase 4: Utils ✓
- [ ] Implement `doc_to_text()`
- [ ] Implement `extract_moves_from_response()`
- [ ] Implement `process_results()`
- [ ] Implement custom metrics

### Phase 5: Testing ✓
- [ ] Unit tests for simulator
- [ ] Unit tests for parsing
- [ ] Integration tests
- [ ] Manual testing with CLI

### Phase 6: Documentation ✓
- [ ] Write README.md
- [ ] Add examples
- [ ] Document metrics
- [ ] Add to main tasks README

## CLI Commands

### Generate sample outputs
```bash
python -m scripts.write_out \
    --output_base_path ./samples.txt \
    --tasks tower_of_hanoi_3 \
    --sets test \
    --num_fewshot 0 \
    --num_examples 5
```

### Run evaluation
```bash
# Single task
python -m lm_eval --model hf \
    --model_args pretrained=gpt2 \
    --tasks tower_of_hanoi_3 \
    --limit 10

# All variants
python -m lm_eval --model hf \
    --model_args pretrained=gpt2 \
    --tasks tower_of_hanoi \
    --limit 50
```

### Run tests
```bash
pytest tests/test_tower_of_hanoi.py -v
```

## Prompt Template Structure

```
[SYSTEM PROMPT]
- Problem description
- Rules (1-3)
- Example solution (N=3)
- Format requirements

[USER PROMPT]
- Specific instance with N disks
- Initial configuration
- Goal configuration  
- Rules reminder
- Request for solution
```

## Expected Model Output
```
[Optional reasoning/explanation]

moves = [[1, 0, 2], [2, 0, 1], [1, 2, 1], [3, 0, 2], 
         [1, 1, 0], [2, 1, 2], [1, 0, 2]]
```

## Validation Flow
```
Model Response
    ↓
Extract Moves (regex parsing)
    ↓
Initialize State (N disks on peg 0)
    ↓
For each move:
    - Validate move
    - Execute if valid
    - Record errors
    ↓
Check if goal reached
    ↓
Compute metrics
```

## Error Types

| Error Type | Example | Detection |
|------------|---------|-----------|
| Invalid peg | `from_peg=3` | Peg boundary check |
| Empty source | Move from empty peg | Source check |
| Wrong disk | Move disk not on top | Top disk check |
| Size violation | Larger on smaller | Size constraint |
| Malformed | `[1, 0]` (missing to_peg) | Parsing |
| No moves | Empty response | Parsing |

## Success Metrics (MVP)

- [ ] Simulator accuracy: 100% on known test cases
- [ ] Parsing success: >95% on varied formats
- [ ] Task integration: Runs via `lm_eval` CLI
- [ ] Test coverage: >80%
- [ ] Documentation: Complete with examples

## Common Pitfalls to Avoid

1. **Off-by-one errors**: Pegs are 0-indexed, disks are 1-indexed
2. **State mutation**: Deep copy state when needed
3. **Parsing edge cases**: Handle responses without "moves ="
4. **Metric aggregation**: Use correct aggregation functions
5. **Max tokens**: Set high enough for N≥6 (127+ moves)

## Code Style

```python
# Use type hints
def validate_move(disk: int, from_peg: int, to_peg: int) -> tuple[bool, str]:
    pass

# Document functions
def process_results(doc: dict, results: list) -> dict:
    """
    Process model output and validate solution.
    
    Args:
        doc: Problem instance with num_disks, initial_state, etc.
        results: List of model responses
        
    Returns:
        Dictionary of metrics for this instance
    """
    pass

# Use descriptive variable names
num_valid_moves = 0  # Good
n = 0  # Bad (unclear)
```

## Dependencies

**Required:**
- Python 3.8+
- lm_eval framework
- Standard library only (json, re, typing, dataclasses)

**No external dependencies needed** ✓

## Timeline Estimate

- **Phase 1 (Dataset)**: 1 day
- **Phase 2 (Simulator)**: 2-3 days
- **Phase 3 (Config)**: 1 day
- **Phase 4 (Utils)**: 2-3 days
- **Phase 5 (Testing)**: 2 days
- **Phase 6 (Docs)**: 1 day

**Total**: ~10-12 days for complete implementation

## Next Steps

1. Start with dataset generator (easiest, no dependencies)
2. Build simulator with comprehensive tests
3. Implement utils functions incrementally
4. Create YAML configs
5. Integration testing
6. Documentation and examples

---

**Ready to implement? Start with Phase 1!**

