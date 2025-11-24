# Tower of Hanoi Implementation Plan for LM-Evaluation-Harness

## Overview
This plan outlines the implementation of the Tower of Hanoi puzzle evaluation task for the lm-evaluation-harness framework. The task will evaluate reasoning models' sequential reasoning, planning capabilities, and constraint satisfaction abilities through a classic recursive puzzle.

## Project Structure

```
lm_eval/tasks/tower_of_hanoi/
├── __init__.py
├── README.md
├── tower_of_hanoi.yaml          # Main task configuration (generated instances)
├── tower_of_hanoi_3.yaml        # 3-disk configuration
├── tower_of_hanoi_4.yaml        # 4-disk configuration
├── tower_of_hanoi_5.yaml        # 5-disk configuration
├── tower_of_hanoi_6.yaml        # 6-disk configuration
├── tower_of_hanoi_7.yaml        # 7-disk configuration
├── _default_template.yaml       # Shared configuration template
├── _group.yaml                  # Group configuration for all variants
├── simulator.py                 # Tower of Hanoi simulator/validator
├── utils.py                     # Utility functions (prompt generation, result processing)
└── dataset_generator.py         # Script to generate problem instances
```

---

## Phase 1: Dataset Creation

### 1.1 Problem Instance Generator (`dataset_generator.py`)

**Purpose:** Create a dataset of Tower of Hanoi problem instances with varying difficulty levels.

**Implementation:**
- Generate problem instances for N=3,4,5,6,7 disks
- Each instance contains:
  - `problem_id`: Unique identifier (e.g., "hanoi_3_001")
  - `num_disks`: Number of disks (N)
  - `initial_state`: [[N, ..., 2, 1], [], []] 
  - `goal_state`: [[], [], [N, ..., 2, 1]]
  - `optimal_moves`: 2^N - 1 (for reference, not required)
  
**Dataset Format:**
```python
{
    "problem_id": "hanoi_3_001",
    "num_disks": 3,
    "initial_state": [[3, 2, 1], [], []],
    "goal_state": [[], [], [3, 2, 1]],
    "optimal_moves": 7
}
```

**Storage:**
- Save as JSON or JSONL files in `lm_eval/tasks/tower_of_hanoi/data/`
- Separate files for each difficulty level: `hanoi_N.jsonl`
- For simplicity, can generate 50-100 instances per difficulty level (all instances for a given N are equivalent in terms of initial/goal states, but having multiple instances helps with statistical significance)

**Rationale:** While all Tower of Hanoi instances with N disks are structurally identical, having multiple instances in the dataset enables better statistical analysis and allows for potential future variations (e.g., different starting pegs, partial solutions).

---

## Phase 2: Simulator Implementation

### 2.1 Tower of Hanoi Simulator (`simulator.py`)

**Purpose:** Validate move sequences and track puzzle state.

**Core Components:**

#### A. TowerOfHanoiState Class
```python
class TowerOfHanoiState:
    """
    Manages the state of Tower of Hanoi puzzle.
    """
    def __init__(self, num_disks: int):
        # Initialize with all disks on peg 0
        self.num_disks = num_disks
        self.pegs = [list(range(num_disks, 0, -1)), [], []]
        self.move_count = 0
        
    def get_state(self) -> list:
        """Return current state of all three pegs."""
        
    def is_valid_move(self, disk: int, from_peg: int, to_peg: int) -> tuple[bool, str]:
        """
        Validate a single move against puzzle constraints.
        Returns: (is_valid, error_message)
        """
        
    def execute_move(self, disk: int, from_peg: int, to_peg: int) -> bool:
        """Execute a move if valid, return success status."""
        
    def is_goal_reached(self) -> bool:
        """Check if goal state (all disks on peg 2) is achieved."""
```

#### B. Move Validation Logic
Implement four-layer validation:
1. **Peg Boundary Check**: Verify from_peg and to_peg are in [0, 1, 2]
2. **Source Peg Check**: Verify from_peg contains at least one disk
3. **Top Disk Check**: Verify the specified disk is the topmost disk on from_peg
4. **Size Ordering Check**: Verify no larger disk is placed on smaller disk

#### C. Solution Validator
```python
class HanoiSolutionValidator:
    """
    Validates complete move sequences for Tower of Hanoi.
    """
    def validate_solution(self, 
                         num_disks: int, 
                         moves: list[list[int]]) -> dict:
        """
        Validate a complete solution.
        Returns dict with:
        - is_valid: bool
        - goal_reached: bool
        - num_valid_moves: int
        - total_moves: int
        - first_error_index: int or None
        - error_messages: list[str]
        - final_state: list
        """
```

**Key Features:**
- Step-by-step validation with detailed error reporting
- Track state after each move
- Identify first invalid move
- Provide clear error messages for debugging

---

## Phase 3: Task Configuration

### 3.1 YAML Configuration Files

#### A. Default Template (`_default_template.yaml`)
```yaml
# Shared configuration for all Tower of Hanoi variants
dataset_path: json
dataset_name: null
output_type: generate_until
test_split: test
num_fewshot: 0
doc_to_text: !function utils.doc_to_text
doc_to_target: !function utils.doc_to_target
process_results: !function utils.process_results
generation_kwargs:
  until:
    - "\n\n"
    - "Question:"
    - "</s>"
    - "<|im_end|>"
  max_gen_toks: 2048
  do_sample: false
  temperature: 0.0
metric_list:
  - metric: !function utils.hanoi_solution_valid
    aggregation: mean
    higher_is_better: true
  - metric: !function utils.hanoi_goal_reached
    aggregation: mean
    higher_is_better: true
  - metric: !function utils.hanoi_move_accuracy
    aggregation: mean
    higher_is_better: true
  - metric: !function utils.hanoi_first_error_step
    aggregation: mean
    higher_is_better: true
filter_list:
  - name: "extract_moves"
    filter:
      - function: "custom"
        filter_fn: !function utils.extract_moves_from_response
```

#### B. Individual Task Configs
Example: `tower_of_hanoi_3.yaml`
```yaml
task: tower_of_hanoi_3
task_alias: "Tower of Hanoi (3 disks)"
include: _default_template.yaml
dataset_kwargs:
  data_files:
    test: hanoi_3.jsonl
tag:
  - reasoning
  - planning
  - tower_of_hanoi
metadata:
  version: 1.0
  num_disks: 3
  optimal_moves: 7
```

#### C. Group Configuration (`_group.yaml`)
```yaml
group: tower_of_hanoi
group_alias: "Tower of Hanoi Benchmark"
task:
  - tower_of_hanoi_3
  - tower_of_hanoi_4
  - tower_of_hanoi_5
  - tower_of_hanoi_6
  - tower_of_hanoi_7
aggregate_metric_list:
  - metric: hanoi_solution_valid
    aggregation: mean
    weight_by_size: true
  - metric: hanoi_goal_reached
    aggregation: mean
    weight_by_size: true
  - metric: hanoi_move_accuracy
    aggregation: mean
    weight_by_size: true
metadata:
  version: 1.0
  description: "Tower of Hanoi puzzle evaluation suite for sequential reasoning and planning"
```

---

## Phase 4: Utility Functions Implementation

### 4.1 Core Functions (`utils.py`)

#### A. Prompt Generation
```python
def doc_to_text(doc: dict) -> str:
    """
    Generate the system + user prompt for a Tower of Hanoi instance.
    
    Includes:
    - System prompt with problem description
    - Rules and constraints
    - Example solution (for 3 disks)
    - Formatting requirements
    - User prompt with specific instance
    """
    system_prompt = get_system_prompt()
    user_prompt = generate_user_prompt(doc)
    return f"{system_prompt}\n\n{user_prompt}"

def get_system_prompt() -> str:
    """
    Return the complete system prompt with:
    - Problem statement
    - Movement rules
    - Example demonstration
    - Format requirements
    """
    
def generate_user_prompt(doc: dict) -> str:
    """
    Generate instance-specific user prompt showing:
    - Number of disks
    - Initial configuration
    - Goal configuration
    - Rules (repeated for clarity)
    """
```

#### B. Response Parsing
```python
def extract_moves_from_response(resps: list[list[str]], 
                                docs: list[dict]) -> list[list[list[int]]]:
    """
    Extract move sequences from model responses.
    
    Handles various formats:
    - moves = [[1, 0, 2], [2, 0, 1], ...]
    - List format without 'moves ='
    - Responses with explanation text
    
    Returns: List of move sequences (list of [disk_id, from_peg, to_peg])
    """
```

#### C. Result Processing
```python
def process_results(doc: dict, results: list) -> dict:
    """
    Process model output and validate solution.
    
    Steps:
    1. Extract moves from response
    2. Validate moves using HanoiSolutionValidator
    3. Return metrics for this instance
    
    Returns:
        {
            'hanoi_solution_valid': 1 or 0,
            'hanoi_goal_reached': 1 or 0,
            'hanoi_move_accuracy': float (0-1),
            'hanoi_first_error_step': int or -1,
            'hanoi_num_moves': int
        }
    """
```

#### D. Custom Metrics
```python
def hanoi_solution_valid(items: list) -> float:
    """Percentage of solutions with all valid moves and goal reached."""
    
def hanoi_goal_reached(items: list) -> float:
    """Percentage of solutions that reached the goal state."""
    
def hanoi_move_accuracy(items: list) -> float:
    """Average per-move accuracy across all solutions."""
    
def hanoi_first_error_step(items: list) -> float:
    """Average step number where first error occurs (-1 if no errors)."""
```

---

## Phase 5: Testing & Validation

### 5.1 Unit Tests

Create `tests/test_tower_of_hanoi.py`:

#### A. Simulator Tests
- Test valid move sequences
- Test invalid moves (wrong disk, wrong peg, size constraint violation)
- Test goal state detection
- Test state tracking

#### B. Parser Tests
- Test extraction of move sequences from various response formats
- Test handling of malformed responses
- Test extraction with explanatory text

#### C. Integration Tests
- Test complete evaluation pipeline with sample responses
- Test metric calculation
- Test aggregation across multiple instances

### 5.2 Manual Validation
```bash
# Test with single task
python -m lm_eval --model hf \
    --model_args pretrained=gpt2 \
    --tasks tower_of_hanoi_3 \
    --limit 5

# Test entire group
python -m lm_eval --model hf \
    --model_args pretrained=gpt2 \
    --tasks tower_of_hanoi \
    --limit 5

# Generate sample outputs for inspection
python -m scripts.write_out \
    --output_base_path ./hanoi_samples.txt \
    --tasks tower_of_hanoi_3 \
    --sets test \
    --num_fewshot 0 \
    --num_examples 5
```

---

## Phase 6: Documentation

### 6.1 README.md Structure

```markdown
# Tower of Hanoi

## Description
Evaluation task for the Tower of Hanoi puzzle, designed to assess sequential 
reasoning, planning capabilities, and constraint satisfaction in language models.

## Problem Description
[Full description of the puzzle, rules, and evaluation criteria]

## Tasks
- `tower_of_hanoi_3`: 3 disks (7 optimal moves)
- `tower_of_hanoi_4`: 4 disks (15 optimal moves)
- `tower_of_hanoi_5`: 5 disks (31 optimal moves)
- `tower_of_hanoi_6`: 6 disks (63 optimal moves)
- `tower_of_hanoi_7`: 7 disks (127 optimal moves)
- `tower_of_hanoi`: Group encompassing all variants

## Metrics
- **hanoi_solution_valid**: Percentage of completely valid and correct solutions
- **hanoi_goal_reached**: Percentage of solutions reaching goal state
- **hanoi_move_accuracy**: Average percentage of valid moves per solution
- **hanoi_first_error_step**: Average step where first error occurs

## Citation
[If based on a paper, include citation]

## Changelog
- [Date] Version 1.0: Initial implementation
```

---

## Phase 7: Advanced Features (Optional Enhancements)

### 7.1 Variants
- **Different starting configurations**: Start with disks on different pegs
- **Partial solutions**: Provide initial moves and ask model to complete
- **Constraint variations**: 4 pegs instead of 3 (Tower of Hanoi Plus)
- **Subgoal evaluation**: Evaluate intermediate reasoning steps

### 7.2 Enhanced Metrics
- **Optimality score**: Compare move count to optimal solution
- **Efficiency ratio**: (optimal_moves / actual_moves)
- **Recovery ability**: Can model fix errors after invalid move?
- **Planning depth**: Analyze if model shows evidence of recursive thinking

### 7.3 Few-Shot Learning Support
- Add few-shot examples for smaller instances (e.g., N=2 or N=3)
- Create `tower_of_hanoi_4_fewshot.yaml` with N=3 examples

---

## Implementation Timeline

### Week 1: Foundation
- [ ] Set up project structure
- [ ] Implement dataset generator
- [ ] Create sample datasets (N=3,4,5)

### Week 2: Core Logic
- [ ] Implement TowerOfHanoiState class
- [ ] Implement move validation logic
- [ ] Implement HanoiSolutionValidator
- [ ] Write unit tests for simulator

### Week 3: Integration
- [ ] Implement utils.py functions
- [ ] Create YAML configurations
- [ ] Test response parsing
- [ ] Implement custom metrics

### Week 4: Testing & Polish
- [ ] Integration testing with framework
- [ ] Test with actual LMs
- [ ] Write documentation
- [ ] Create examples and sample outputs
- [ ] Code review and refinement

---

## Key Design Decisions

### 1. Response Format
**Decision:** Require strict format `moves = [[disk, from, to], ...]`

**Rationale:**
- Clear, unambiguous format
- Easy to parse reliably
- Matches example in system prompt
- Reduces ambiguity in evaluation

**Alternative:** Could support multiple formats (natural language, step-by-step), but increases complexity.

### 2. Evaluation Criteria
**Decision:** Focus on correctness, not optimality

**Rationale:**
- Optimality is very difficult (exponential moves required)
- Correctness demonstrates understanding of constraints
- More forgiving for smaller models
- Aligns with problem description requirements

### 3. Error Handling
**Decision:** Continue validation after first error but record error location

**Rationale:**
- Provides more diagnostic information
- Allows partial credit via move_accuracy metric
- Helps identify common failure modes
- More informative for model developers

### 4. Difficulty Levels
**Decision:** Start with N=3 to N=7

**Rationale:**
- N=3: Trivial (7 moves) - baseline
- N=4: Easy (15 moves) - most models should handle
- N=5: Medium (31 moves) - challenging for smaller models
- N=6: Hard (63 moves) - difficult for most models
- N=7: Very Hard (127 moves) - likely only very large/advanced models
- Beyond N=7 becomes impractical due to exponential growth

---

## Dependencies

### Python Packages
- Standard library: `json`, `re`, `typing`, `dataclasses`
- Framework: `lm_eval` (existing)
- No external dependencies required

### Data Requirements
- Minimal: ~1KB per difficulty level
- Total dataset size: <50KB
- Can be generated on-the-fly if needed

---

## Success Criteria

### Minimum Viable Product (MVP)
- [ ] Simulator correctly validates move sequences
- [ ] Parser extracts moves from model responses
- [ ] At least 3 difficulty levels (N=3,4,5) working
- [ ] Basic metrics implemented and accurate
- [ ] Task runs successfully via `lm_eval` CLI
- [ ] Unit tests pass
- [ ] Documentation complete

### Extended Goals
- [ ] All 5 difficulty levels (N=3-7)
- [ ] Comprehensive test coverage (>90%)
- [ ] Few-shot examples working
- [ ] Advanced metrics implemented
- [ ] Tested with multiple model types
- [ ] Example outputs in documentation
- [ ] Integration into main task registry

---

## Potential Challenges & Solutions

### Challenge 1: Response Parsing Variability
**Problem:** Models may format responses differently
**Solution:** 
- Implement robust regex-based parsing
- Support common variations
- Provide clear format in prompt
- Test with multiple models early

### Challenge 2: Long Sequence Generation
**Problem:** For N≥6, sequences become very long (>63 moves)
**Solution:**
- Set appropriate `max_gen_toks` (2048+)
- Consider truncation handling
- May need to limit to N≤6 for practical evaluation

### Challenge 3: Partial Credit
**Problem:** Models might get first few moves right then fail
**Solution:**
- Implement `move_accuracy` metric
- Track `first_error_step` metric
- Both provide insight into partial understanding

### Challenge 4: Dataset Size
**Problem:** Need sufficient instances for statistical validity
**Solution:**
- For Tower of Hanoi, all instances with N disks are equivalent
- Can generate many instances computationally
- 50-100 instances per difficulty should suffice

---

## Testing Strategy

### Unit Testing
```python
# Test simulator
test_valid_move_execution()
test_invalid_move_detection()
test_goal_state_detection()
test_state_consistency()

# Test parser
test_extract_standard_format()
test_extract_with_explanation()
test_handle_malformed_response()
test_extract_partial_solution()

# Test metrics
test_solution_valid_calculation()
test_goal_reached_calculation()
test_move_accuracy_calculation()
```

### Integration Testing
```python
# Test end-to-end flow
test_complete_evaluation_pipeline()
test_with_correct_solution()
test_with_incorrect_solution()
test_with_partial_solution()
```

### Manual Testing
```bash
# Verify prompts look correct
python -m scripts.write_out --tasks tower_of_hanoi_3 --num_examples 2

# Run on small model
python -m lm_eval --model hf --model_args pretrained=gpt2 \
    --tasks tower_of_hanoi_3 --limit 5

# Test group
python -m lm_eval --model hf --model_args pretrained=gpt2 \
    --tasks tower_of_hanoi --limit 10
```

---

## Code Quality Standards

### Style Guidelines
- Follow PEP 8 conventions
- Type hints for all function signatures
- Docstrings for all public functions
- Clear variable names
- Comments for complex logic

### Documentation Requirements
- Module-level docstrings
- Function docstrings with Args/Returns
- Inline comments for non-obvious logic
- README with examples
- CHANGELOG for version tracking

### Testing Requirements
- Unit tests for all core functions
- Integration tests for evaluation pipeline
- Edge case coverage
- Minimum 80% code coverage target

---

## Future Enhancements

### Potential Extensions
1. **Multi-task Tower of Hanoi**: Multiple puzzles in sequence
2. **Interactive Tower of Hanoi**: Step-by-step solution with feedback
3. **Visualization**: Generate state diagrams for solutions
4. **Explanation Analysis**: Evaluate reasoning in model's explanation
5. **Adversarial Variants**: Trick questions or misleading setups
6. **Transfer Learning**: Test if models can generalize from N=3 to larger N

### Research Directions
1. Analyze which models use recursive strategies
2. Correlation between model size and performance
3. Impact of chain-of-thought prompting
4. Few-shot vs zero-shot performance comparison

---

## Appendix: Example Outputs

### Example System Prompt
```
You are a helpful assistant. Solve this puzzle for me.

There are three pegs and n disks of different sizes stacked on the first peg...
[Full system prompt as specified in requirements]
```

### Example User Prompt (N=3)
```
I have a puzzle with 3 disks of different sizes with

Initial configuration:
• Peg 0: 3 (bottom), 2, 1 (top)
• Peg 1: (empty)
• Peg 2: (empty)

Goal configuration:
• Peg 0: (empty)
• Peg 1: (empty)
• Peg 2: 3 (bottom), 2, 1 (top)

Rules:
• Only one disk can be moved at a time.
• Only the top disk from any stack can be moved.
• A larger disk may not be placed on top of a smaller disk.

Find the sequence of moves to transform the initial configuration into the goal configuration.
```

### Example Correct Response
```
moves = [[1, 0, 2], [2, 0, 1], [1, 2, 1], [3, 0, 2], [1, 1, 0], [2, 1, 2], [1, 0, 2]]
```

### Example Metrics Output
```
{
  "tower_of_hanoi_3": {
    "hanoi_solution_valid": 0.85,
    "hanoi_goal_reached": 0.90,
    "hanoi_move_accuracy": 0.93,
    "hanoi_first_error_step": 4.5
  }
}
```

---

## Conclusion

This implementation plan provides a comprehensive roadmap for adding the Tower of Hanoi evaluation task to the lm-evaluation-harness framework. The modular design allows for incremental development and testing, while the clear separation of concerns (simulator, utils, configuration) ensures maintainability and extensibility.

The task will provide valuable insights into models' sequential reasoning, planning, and constraint satisfaction capabilities, filling an important gap in the current evaluation landscape for long-range reasoning tasks.

