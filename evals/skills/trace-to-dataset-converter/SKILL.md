---
name: trace-to-dataset-converter
description: >
  Convert trace files (nested JSON with spans, embeddings, retrieval)
  into flat Truesight-compatible datasets. Use when you have raw traces
  from an AI system and need to prepare them for error analysis or
  quantitative evaluation in Truesight.
metadata:
  arguments: "--traces <traces.json> --output_format <error_analysis|eval_tuning|held_out_eval> --output <output.json>"
---

# Trace-to-Dataset Converter

## Overview

Use this skill to convert raw AI system trace files into flat Truesight-compatible datasets. Trace files typically contain nested structures with execution spans (embeddings, retrieval, LLM calls) that are not needed for evaluation datasets.

This skill supports three output formats corresponding to the three stages of the evaluation workflow:

1. **error_analysis** - For qualitative review and error categorization
2. **eval_tuning** - For building and calibrating evaluators with labeled examples
3. **held_out_eval** - For running a built evaluator against unseen data

---

## Inputs Required

- `traces`: Path to the trace JSON file. Expected structure:
  ```json
  {
    "results": [
      {
        "case_id": "...",
        "user_query": "...",
        "actual_output": "...",
        "expected_behavior": "..." or "expected_output": "...",
        "trace": { "spans": [...] }
      }
    ]
  }
  ```
- `output_format`: One of `error_analysis`, `eval_tuning`, or `held_out_eval`
- `output`: Path for the output JSON file

## How to Access Inputs

- Read the trace file from the provided path
- Parse the JSON and extract the `results` array
- Each result contains the core fields needed; the `trace` object (spans, embeddings, retrieval docs) should be dropped

---

## Instructions

### Step 1: Read and validate the trace file

Open and parse the trace JSON. Verify it has a `results` array. For each result, identify which fields are present:

- `user_query` (required)
- `actual_output` (required)
- `expected_behavior` (qualitative traces - describes what should have happened)
- `expected_output` (quantitative traces - the ground truth answer)
- `case_id`, `case_name`, `source_testset` (metadata, optional)
- `trace` (execution details - always drop this)

### Step 2: Determine the field mapping based on output format

#### For `error_analysis`:
| Source Field | Target Column |
|---|---|
| `user_query` | `student_question` |
| `actual_output` | `ai_tutor_response` |
| `expected_behavior` OR `expected_output` | `expected_behavior` |

No judgment columns. Learners will manually annotate.

#### For `eval_tuning`:
| Source Field | Target Column |
|---|---|
| `user_query` | `student_question` |
| `actual_output` | `ai_tutor_response` |
| `expected_output` | `expected_output` |
| (computed) | `is_accurate` |
| (empty or computed) | `expert_notes` |

The `is_accurate` column should be pre-filled with Pass/Fail based on whether the actual output is factually consistent with the expected output. Use your judgment to compare semantic equivalence, not surface similarity.

#### For `held_out_eval`:
| Source Field | Target Column |
|---|---|
| `user_query` | `student_question` |
| `actual_output` | `ai_tutor_response` |
| `expected_output` | `expected_output` |
| (empty) | `is_accurate` |
| (empty) | `expert_notes` |

Same columns as `eval_tuning` but with empty judgment columns. These will be scored by the evaluator.

### Step 3: Extract and transform

For each result in the `results` array:
1. Extract the mapped fields
2. Drop the `trace` object entirely (spans, embeddings, retrieval documents, latency, token counts)
3. Drop `case_id`, `case_name`, `source_testset` (not needed in Truesight datasets)
4. If `expected_behavior` and `expected_output` are both present, prefer `expected_behavior` for error_analysis format and `expected_output` for eval formats
5. **Clean LaTeX math notation** from `actual_output` before writing to `ai_tutor_response`. LLM outputs often contain LaTeX (e.g. `\text{}`, `\frac{}{}`, `\rightarrow`) that doesn't render in the Truesight UI. Convert to plain text math:
   - `\text{H}_2` → `H_2`
   - `\frac{mass}{volume}` → `(mass)/(volume)`
   - `\rightarrow` → `→`, `\rightleftharpoons` → `⇌`
   - `\times` → `×`, `\div` → `÷`, `\approx` → `≈`
   - `\Delta` → `Δ`, `\circ` → `°`
   - Remove display math delimiters `\[...\]` and inline `\(...\)`
6. **Preserve column order** in the output JSON: `student_question` must come first, then `ai_tutor_response`, then remaining columns. Truesight displays columns in the order they appear in the JSON.

### Step 4: For eval_tuning format, make Pass/Fail judgments

Compare each `actual_output` against `expected_output`:
- **Pass**: The actual output is factually consistent with the expected output. It may include additional correct detail, use different wording, or explain more thoroughly, but the core facts match.
- **Fail**: The actual output contains factual errors, is missing critical information from the expected output, or contradicts the expected output.

For approximately half the rows, write brief `expert_notes` explaining the judgment. Leave the rest empty for learners to practice writing their own notes.

### Step 5: Write the output

Write the result as a JSON array of flat objects to the output path.

---

## Output Format

A JSON array where each element is a flat object. Example for `eval_tuning`:

```json
[
  {
    "student_question": "What is density in chemistry?",
    "ai_tutor_response": "Density is a physical property defined as mass divided by volume...",
    "expected_output": "Density is the amount of mass in a given volume of a substance...",
    "is_accurate": "Pass",
    "expert_notes": "Correctly defines density with the proper formula."
  }
]
```

---

## Quality Checks

1. Verify no `trace` data leaked into the output (no spans, embeddings, retrieval docs)
2. Verify all rows have the expected columns
3. For `eval_tuning`, verify every row has a Pass or Fail judgment
4. For `held_out_eval`, verify all judgment columns are empty strings
5. Verify the output is valid JSON
