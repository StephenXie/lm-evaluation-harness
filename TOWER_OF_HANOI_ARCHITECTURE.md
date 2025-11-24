# Tower of Hanoi - System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     LM Evaluation Harness                        │
│                         (Framework)                              │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ loads task
             ↓
┌─────────────────────────────────────────────────────────────────┐
│              Tower of Hanoi Task Configuration                   │
│                  (YAML + Python Utils)                           │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─────────┬─────────┬──────────┬─────────────┐
             ↓         ↓         ↓          ↓             ↓
        ┌────────┐ ┌──────┐ ┌────────┐ ┌─────────┐ ┌─────────┐
        │Dataset │ │Utils │ │Simulator│ │Prompts  │ │Metrics  │
        └────────┘ └──────┘ └────────┘ └─────────┘ └─────────┘
```

## Detailed Component Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          EVALUATION FLOW                             │
└──────────────────────────────────────────────────────────────────────┘

1. INITIALIZATION
   ┌─────────────────┐
   │  Load Dataset   │ ← hanoi_N.jsonl files
   │  (HF Datasets)  │
   └────────┬────────┘
            │
            ↓
   ┌─────────────────┐
   │ Process Docs    │ ← process_docs() (optional)
   └────────┬────────┘
            │
            ↓
2. PROMPT GENERATION
   ┌─────────────────┐
   │  doc_to_text()  │ ← Generate system + user prompt
   │                 │   Input: doc = {num_disks, initial_state, ...}
   │                 │   Output: formatted prompt string
   └────────┬────────┘
            │
            ↓
3. MODEL INFERENCE
   ┌─────────────────┐
   │  Language Model │ ← Model generates response
   │   Generation    │   Input: prompt
   │                 │   Output: text with moves
   └────────┬────────┘
            │
            ↓
4. RESPONSE PROCESSING
   ┌─────────────────────────┐
   │ extract_moves_from_     │ ← Parse response text
   │     response()          │   Input: raw text
   │                         │   Output: list of [disk, from, to]
   └────────┬────────────────┘
            │
            ↓
5. VALIDATION
   ┌─────────────────────────┐
   │  HanoiSolution          │ ← Validate move sequence
   │    Validator            │   Input: moves list
   │                         │   Output: validation results
   └────────┬────────────────┘
            │
            ↓
6. METRIC COMPUTATION
   ┌─────────────────────────┐
   │  process_results()      │ ← Compute per-instance metrics
   │                         │   Returns: dict of metric values
   └────────┬────────────────┘
            │
            ↓
7. AGGREGATION
   ┌─────────────────────────┐
   │  Aggregate Metrics      │ ← Mean across all instances
   │  (mean, etc.)           │   Final task scores
   └─────────────────────────┘
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA STRUCTURES                           │
└─────────────────────────────────────────────────────────────────┘

DATASET INSTANCE (doc)
{
  "problem_id": "hanoi_3_001",
  "num_disks": 3,
  "initial_state": [[3,2,1], [], []],
  "goal_state": [[], [], [3,2,1]],
  "optimal_moves": 7
}
        ↓ doc_to_text()
        
PROMPT STRING
"You are a helpful assistant. Solve this puzzle for me.
There are three pegs and n disks...
[system prompt]

I have a puzzle with 3 disks...
[user prompt]"
        ↓ Model Generation
        
MODEL RESPONSE
"To solve this puzzle, I need to move disks following the rules.

moves = [[1,0,2], [2,0,1], [1,2,1], [3,0,2], 
         [1,1,0], [2,1,2], [1,0,2]]"
        ↓ extract_moves()
        
PARSED MOVES
[
  [1, 0, 2],  # Move disk 1 from peg 0 to peg 2
  [2, 0, 1],  # Move disk 2 from peg 0 to peg 1
  [1, 2, 1],  # Move disk 1 from peg 2 to peg 1
  [3, 0, 2],  # Move disk 3 from peg 0 to peg 2
  [1, 1, 0],  # Move disk 1 from peg 1 to peg 0
  [2, 1, 2],  # Move disk 2 from peg 1 to peg 2
  [1, 0, 2]   # Move disk 1 from peg 0 to peg 2
]
        ↓ validate_solution()
        
VALIDATION RESULT
{
  "is_valid": True,
  "goal_reached": True,
  "num_valid_moves": 7,
  "total_moves": 7,
  "first_error_index": None,
  "error_messages": [],
  "final_state": [[], [], [3,2,1]]
}
        ↓ process_results()
        
INSTANCE METRICS
{
  "hanoi_solution_valid": 1,
  "hanoi_goal_reached": 1,
  "hanoi_move_accuracy": 1.0,
  "hanoi_first_error_step": -1,
  "hanoi_num_moves": 7
}
        ↓ aggregate (mean)
        
FINAL METRICS
{
  "hanoi_solution_valid": 0.85,
  "hanoi_goal_reached": 0.90,
  "hanoi_move_accuracy": 0.93,
  "hanoi_first_error_step": 4.2
}
```

## Module Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      MODULE ORGANIZATION                          │
└──────────────────────────────────────────────────────────────────┘

simulator.py
├── TowerOfHanoiState
│   ├── __init__(num_disks)
│   ├── get_state() → list[list[int]]
│   ├── is_valid_move(disk, from, to) → (bool, str)
│   ├── execute_move(disk, from, to) → bool
│   └── is_goal_reached() → bool
│
└── HanoiSolutionValidator
    ├── __init__()
    └── validate_solution(num_disks, moves) → dict
        ├── _validate_single_move()
        ├── _track_state()
        └── _check_goal()

utils.py
├── Prompt Generation
│   ├── doc_to_text(doc) → str
│   ├── doc_to_target(doc) → str
│   ├── get_system_prompt() → str
│   └── generate_user_prompt(doc) → str
│
├── Response Processing
│   ├── extract_moves_from_response(resps, docs) → list
│   ├── parse_moves_format(text) → list
│   └── clean_response(text) → str
│
├── Result Processing
│   └── process_results(doc, results) → dict
│       ├── extract_moves()
│       ├── validate_moves()
│       └── compute_metrics()
│
└── Custom Metrics
    ├── hanoi_solution_valid(items) → float
    ├── hanoi_goal_reached(items) → float
    ├── hanoi_move_accuracy(items) → float
    └── hanoi_first_error_step(items) → float

dataset_generator.py
├── generate_hanoi_dataset(num_disks, num_instances) → list
├── create_instance(num_disks, instance_id) → dict
└── save_dataset(instances, output_path)
```

## State Machine for Validation

```
┌────────────────────────────────────────────────────────────────┐
│              MOVE VALIDATION STATE MACHINE                      │
└────────────────────────────────────────────────────────────────┘

                    START
                      │
                      ↓
            ┌─────────────────────┐
            │ Check Peg Boundary  │
            │ (0 ≤ peg ≤ 2)       │
            └──────┬──────────────┘
                   │
         ┌─────────┴─────────┐
         │ Valid              │ Invalid
         ↓                    ↓
┌──────────────────┐   ┌──────────────┐
│ Check Source     │   │ Return Error │
│ Has Disks        │   │ "Invalid peg"│
└────┬─────────────┘   └──────────────┘
     │
     │ Valid
     ↓
┌──────────────────┐
│ Check Disk Is    │
│ Topmost on       │
│ Source Peg       │
└────┬─────────────┘
     │
     │ Valid
     ↓
┌──────────────────┐
│ Check Size       │
│ Constraint       │
│ (No larger on    │
│  smaller)        │
└────┬─────────────┘
     │
     │ Valid
     ↓
┌──────────────────┐
│ Execute Move     │
│ Update State     │
└────┬─────────────┘
     │
     ↓
   SUCCESS
```

## Simulator State Representation

```
┌──────────────────────────────────────────────────────────────┐
│                  STATE REPRESENTATION                         │
└──────────────────────────────────────────────────────────────┘

Initial State (N=4):
┌─────┬─────┬─────┐
│ Peg │ Peg │ Peg │
│  0  │  1  │  2  │
├─────┼─────┼─────┤
│  1  │     │     │  ← Top (smallest disk)
│  2  │     │     │
│  3  │     │     │
│  4  │     │     │  ← Bottom (largest disk)
└─────┴─────┴─────┘

State = [[4,3,2,1], [], []]


After Move [1, 0, 2]:  # Move disk 1 from peg 0 to peg 2
┌─────┬─────┬─────┐
│ Peg │ Peg │ Peg │
│  0  │  1  │  2  │
├─────┼─────┼─────┤
│  2  │     │  1  │
│  3  │     │     │
│  4  │     │     │
└─────┴─────┴─────┘

State = [[4,3,2], [], [1]]


Goal State:
┌─────┬─────┬─────┐
│ Peg │ Peg │ Peg │
│  0  │  1  │  2  │
├─────┼─────┼─────┤
│     │     │  1  │
│     │     │  2  │
│     │     │  3  │
│     │     │  4  │
└─────┴─────┴─────┘

State = [[], [], [4,3,2,1]]
```

## Configuration Hierarchy

```
┌──────────────────────────────────────────────────────────────┐
│                 YAML CONFIGURATION STRUCTURE                  │
└──────────────────────────────────────────────────────────────┘

_default_template.yaml (Base Configuration)
├── dataset_path: json
├── output_type: generate_until
├── doc_to_text: !function utils.doc_to_text
├── process_results: !function utils.process_results
├── metric_list: [...]
├── generation_kwargs: {...}
└── filter_list: [...]

              ↓ included by

tower_of_hanoi_3.yaml (Specific Task)
├── task: tower_of_hanoi_3
├── include: _default_template.yaml
├── dataset_kwargs:
│   └── data_files:
│       └── test: hanoi_3.jsonl
├── tag: [reasoning, planning, tower_of_hanoi]
└── metadata:
    ├── version: 1.0
    └── num_disks: 3

              ↓ grouped by

_group.yaml (Task Group)
├── group: tower_of_hanoi
├── task:
│   ├── tower_of_hanoi_3
│   ├── tower_of_hanoi_4
│   ├── tower_of_hanoi_5
│   ├── tower_of_hanoi_6
│   └── tower_of_hanoi_7
└── aggregate_metric_list: [...]
```

## Validation Algorithm Flowchart

```
┌────────────────────────────────────────────────────────────────┐
│              SOLUTION VALIDATION ALGORITHM                      │
└────────────────────────────────────────────────────────────────┘

Input: num_disks, moves_list
│
├─ Initialize state: pegs = [[N,...,2,1], [], []]
├─ Initialize counters: valid=0, total=0, first_error=-1
│
└─ For each move in moves_list:
   │
   ├─ total += 1
   │
   ├─ Parse move: [disk, from_peg, to_peg]
   │  │
   │  ├─ If parsing fails:
   │  │  ├─ Record error
   │  │  └─ Continue to next move
   │  │
   │  └─ If parsing succeeds:
   │     │
   │     └─ Validate move:
   │        │
   │        ├─ Check peg boundaries (0-2)
   │        │  └─ If invalid: record error, continue
   │        │
   │        ├─ Check source peg has disks
   │        │  └─ If empty: record error, continue
   │        │
   │        ├─ Check disk is topmost on source
   │        │  └─ If not topmost: record error, continue
   │        │
   │        ├─ Check size constraint on destination
   │        │  └─ If violated: record error, continue
   │        │
   │        └─ If all checks pass:
   │           ├─ Execute move (update state)
   │           └─ valid += 1
   │
   └─ After all moves processed:
      │
      ├─ Check if goal reached: pegs[2] == [N,...,2,1]
      │
      └─ Return:
         ├─ is_valid: (valid == total) && goal_reached
         ├─ goal_reached: bool
         ├─ num_valid_moves: valid
         ├─ total_moves: total
         ├─ move_accuracy: valid / total
         ├─ first_error_index: (or -1)
         ├─ error_messages: [...]
         └─ final_state: pegs
```

## Metric Computation Flow

```
┌────────────────────────────────────────────────────────────────┐
│                  METRICS COMPUTATION FLOW                       │
└────────────────────────────────────────────────────────────────┘

Per-Instance (process_results):
┌─────────────────────────────────────────┐
│ Instance 1: doc + model_response        │
│ ↓                                       │
│ validate_solution() →                   │
│   {is_valid: 1, goal: 1, accuracy: 1.0} │
│ ↓                                       │
│ Return instance_metrics                 │
└─────────────────────────────────────────┘

Per-Instance (process_results):
┌─────────────────────────────────────────┐
│ Instance 2: doc + model_response        │
│ ↓                                       │
│ validate_solution() →                   │
│   {is_valid: 0, goal: 0, accuracy: 0.8} │
│ ↓                                       │
│ Return instance_metrics                 │
└─────────────────────────────────────────┘

Per-Instance (process_results):
┌─────────────────────────────────────────┐
│ Instance 3: doc + model_response        │
│ ↓                                       │
│ validate_solution() →                   │
│   {is_valid: 0, goal: 1, accuracy: 0.9} │
│ ↓                                       │
│ Return instance_metrics                 │
└─────────────────────────────────────────┘

              ↓ Aggregation (mean)

Final Task Metrics:
┌─────────────────────────────────────────┐
│ hanoi_solution_valid: (1+0+0)/3 = 0.33 │
│ hanoi_goal_reached: (1+0+1)/3 = 0.67   │
│ hanoi_move_accuracy: (1.0+0.8+0.9)/3   │
│                     = 0.90              │
└─────────────────────────────────────────┘
```

## Error Handling Strategy

```
┌────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING LAYERS                        │
└────────────────────────────────────────────────────────────────┘

Layer 1: Response Parsing
│
├─ Try: Extract moves with primary regex
├─ Catch: Try alternative formats
└─ Fail: Return empty moves list, log warning

Layer 2: Move Validation
│
├─ Try: Validate each move individually
├─ Catch: Record specific validation error
└─ Continue: Process remaining moves (partial credit)

Layer 3: State Management
│
├─ Try: Execute valid moves
├─ Catch: State inconsistency (should not happen)
└─ Fail: Return current state, mark as invalid

Layer 4: Metric Computation
│
├─ Try: Compute all metrics
├─ Catch: Use default values (0 or -1)
└─ Ensure: Always return valid metric dict
```

## Integration Points with LM-Eval Framework

```
┌────────────────────────────────────────────────────────────────┐
│              FRAMEWORK INTEGRATION POINTS                       │
└────────────────────────────────────────────────────────────────┘

1. Task Registration
   └─ YAML file in lm_eval/tasks/tower_of_hanoi/
      └─ Automatically discovered by TaskManager

2. Dataset Loading
   └─ Uses HuggingFace datasets library
      └─ Loads JSON/JSONL files via dataset_kwargs

3. Prompt Generation
   └─ doc_to_text() called by framework
      └─ Receives doc dict, returns string

4. Model Inference
   └─ Framework handles model interaction
      └─ Uses generation_kwargs from YAML

5. Response Processing
   └─ process_results() called by framework
      └─ Receives doc + results, returns metrics dict

6. Metric Aggregation
   └─ Framework applies aggregation functions
      └─ mean, sum, etc. as specified in YAML

7. Result Reporting
   └─ Framework formats and displays results
      └─ Supports various output formats (JSON, stdout, etc.)
```

## Scalability Considerations

```
┌────────────────────────────────────────────────────────────────┐
│                  SCALABILITY ANALYSIS                           │
└────────────────────────────────────────────────────────────────┘

Problem Size (N disks):
├─ State space: O(3^N)
├─ Optimal moves: O(2^N - 1)
└─ Validation time: O(M) where M = number of moves

Practical Limits:
├─ N=3: 7 moves (trivial)
├─ N=4: 15 moves (easy)
├─ N=5: 31 moves (moderate)
├─ N=6: 63 moves (challenging)
├─ N=7: 127 moves (hard, pushing token limits)
└─ N≥8: 255+ moves (impractical for most LLMs)

Memory Usage:
├─ State storage: O(N) per instance
├─ Move list: O(M) per instance
└─ Total: O(N + M) = O(2^N) worst case

Recommendation:
└─ Limit to N≤7 for practical evaluation
```

## Testing Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    TESTING STRATEGY                             │
└────────────────────────────────────────────────────────────────┘

Unit Tests (test_simulator.py)
├─ TowerOfHanoiState
│  ├─ test_initialization
│  ├─ test_valid_moves
│  ├─ test_invalid_moves
│  ├─ test_goal_detection
│  └─ test_state_consistency
│
└─ HanoiSolutionValidator
   ├─ test_correct_solution
   ├─ test_incorrect_solution
   ├─ test_partial_solution
   └─ test_malformed_moves

Unit Tests (test_utils.py)
├─ Prompt Generation
│  ├─ test_doc_to_text
│  ├─ test_system_prompt_format
│  └─ test_user_prompt_format
│
├─ Response Parsing
│  ├─ test_standard_format
│  ├─ test_alternative_formats
│  ├─ test_with_explanation
│  └─ test_malformed_responses
│
└─ Metrics
   ├─ test_solution_valid_metric
   ├─ test_goal_reached_metric
   ├─ test_move_accuracy_metric
   └─ test_first_error_metric

Integration Tests (test_integration.py)
├─ test_end_to_end_correct_solution
├─ test_end_to_end_incorrect_solution
├─ test_yaml_config_loading
├─ test_dataset_loading
└─ test_metric_aggregation

Regression Tests
├─ test_known_good_outputs
└─ test_backward_compatibility
```

---

## Summary

This architecture provides:

✓ **Modularity**: Clear separation of concerns (simulator, utils, config)
✓ **Extensibility**: Easy to add new metrics, variants, or difficulty levels
✓ **Robustness**: Multiple layers of error handling and validation
✓ **Maintainability**: Well-organized code with clear interfaces
✓ **Testability**: Comprehensive testing strategy at all levels
✓ **Integration**: Clean integration with lm-evaluation-harness framework
✓ **Scalability**: Efficient algorithms with clear complexity bounds

The architecture supports both immediate needs (MVP) and future enhancements (advanced metrics, variants, etc.).

