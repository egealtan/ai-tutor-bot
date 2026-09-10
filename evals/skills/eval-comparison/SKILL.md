---
name: eval-comparison
description: >
  Run a Truesight evaluator against a held-out dataset and compare
  AI judge scores to ground truth expectations. Use after building
  an evaluator to verify it is working correctly before deployment.
metadata:
  arguments: "--dataset <held_out_dataset.json> --eval_name <evaluation_name>"
---

# Eval Comparison

## Overview

Use this skill after building an evaluator in Truesight to verify it produces reasonable judgments. It runs the evaluator against a held-out dataset that has ground truth (`expected_output`) and compares the AI judge's Pass/Fail scores against what a human would expect given the ground truth.

This skill helps answer: "Is my evaluator actually catching the errors it should catch, and passing the responses it should pass?"

---

## Inputs Required

- `dataset`: Path to the held-out eval dataset JSON file. Must have columns:
  - `student_question`
  - `ai_tutor_response`
  - `expected_output`
  - `is_accurate` (empty - will be filled by evaluator)
  - `expert_notes` (empty)
- `eval_name`: The name of the Truesight live evaluation to run against

## Prerequisites

- A deployed Truesight live evaluation (created via the UI guided setup or MCP)
- The Truesight MCP server connected

---

## Instructions

### Step 1: Load the held-out dataset

Read the dataset JSON file. Verify it has the expected columns and that `is_accurate` is empty for all rows (these are the rows the evaluator will score).

### Step 2: Identify the Truesight live evaluation

Use the Truesight MCP to list live evaluations and find the one matching `eval_name`. Retrieve its `public_id` and `api_key`.

```
List live evaluations → find the one named <eval_name> → get public_id
```

### Step 3: Run the evaluator on each row

For each row in the dataset, call the Truesight `run_eval` tool with the appropriate inputs:
- `student_question`
- `ai_tutor_response`

Collect the evaluator's judgment (Pass/Fail) and reasoning for each row.

### Step 4: Generate ground truth expectations

For each row, compare `ai_tutor_response` against `expected_output` to determine what the "correct" judgment should be:
- **Expected Pass**: The actual response is factually consistent with the expected output
- **Expected Fail**: The actual response contains errors, omissions, or contradictions relative to the expected output

### Step 5: Build a comparison report

Create a summary comparing evaluator judgments vs ground truth expectations:

```
| Metric | Value |
|---|---|
| Total rows | N |
| Evaluator Pass | N |
| Evaluator Fail | N |
| Agreement with ground truth | N/N (%) |
| False positives (eval Pass, should be Fail) | N |
| False negatives (eval Fail, should be Pass) | N |
```

### Step 6: Identify disagreements

For each row where the evaluator's judgment disagrees with the ground truth expectation, output:
- The student question
- The AI tutor response (truncated)
- The expected output (truncated)
- Evaluator judgment and reasoning
- Expected judgment and why

### Step 7: Provide recommendations

Based on the comparison:
- If agreement is high (>85%): The evaluator is working well. Note any edge cases.
- If agreement is moderate (60-85%): Suggest specific rubric improvements based on the disagreement patterns.
- If agreement is low (<60%): The evaluator needs significant rework. Identify the most common failure patterns and suggest whether the issue is in the rubric, the labeled examples, or both.

---

## Output Format

Print the comparison report directly. Include:

1. Summary table (Step 5)
2. Disagreement details (Step 6)
3. Recommendations (Step 7)

If requested, also write the dataset with evaluator judgments filled in to a new JSON file.

---

## Quality Checks

1. Verify the evaluator returned a judgment for every row
2. Flag any rows where the evaluator returned an error or timeout
3. Ensure ground truth comparison is based on semantic equivalence, not string matching
4. Double-check that false positives and false negatives are correctly classified
