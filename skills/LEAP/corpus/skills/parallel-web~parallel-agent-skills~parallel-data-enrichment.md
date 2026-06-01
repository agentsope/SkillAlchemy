---
name: parallel-data-enrichment
description: "Bulk data enrichment. Adds web-sourced fields (CEO names, funding, contact info) to lists of companies, people, or products. Use for enriching CSV files or inline data. Supports multi-turn: pass --previous-interaction-id from a prior research task to carry context forward."
user-invocable: true
argument-hint: <file or entities> with <fields to add>
compatibility: Requires parallel-cli and internet access.
allowed-tools: Bash(parallel-cli:*)
metadata:
  author: parallel
---

# Data Enrichment

Enrich: $ARGUMENTS

## Before starting

Inform the user that enrichment may take several minutes depending on the number of rows and fields requested.

## Optional: Suggest output columns

If the user gave a vague intent ("enrich these companies with useful info") and you're not sure what columns to add, ask the API for a suggestion before kicking off the run:

```bash
parallel-cli enrich suggest "Find CEO and recent funding info" --json
```

The response is an envelope: `{title, processor, enriched_columns, warnings}`. Extract just the **`enriched_columns` array** (not the whole envelope) and pass it as the value of `--enriched-columns` on `enrich run`, **in place of `--intent`** — the two flags are alternative ways to specify what to enrich, not combined. If `suggest` returned a `processor`, pass it through explicitly via `--processor` on the `run` call (it's a tuned recommendation for the schema). Skip this whole section if the user already specified the fields they want.

> `enrich suggest` requires `parallel-cli` ≥ 0.3.0. If it errors with anything resembling `no such command` / `No such command` / `unknown command`, **do not bail** — skip the suggestion step, fall through to step 1 with `--intent`, complete the run, and mention `parallel-cli update` (or `pipx upgrade parallel-web-tools`) in the final response so the user picks up the feature next time.

## Step 1: Start the enrichment

Use ONE of these command patterns (substitute user's actual data):

For inline data:

```bash
parallel-cli enrich run --data '[{"company": "Google"}, {"company": "Microsoft"}]' --intent "CEO name and founding year" --target "output.csv" --no-wait --json
```

For CSV file:

```bash
parallel-cli enrich run --source-type csv --source "input.csv" --target "output.csv" --source-columns '[{"name": "company", "description": "Company name"}]' --intent "CEO name and founding year" --no-wait --json
```

If this is a **follow-up** to a previous research task and you have its `interaction_id`, add context chaining:

```bash
parallel-cli enrich run --data '...' --intent "..." --target "output.csv" --no-wait --json --previous-interaction-id "$INTERACTION_ID"
```

The enrichment will run with the full context of that prior research — so you can enrich entities discovered earlier without restating what was already found. Note: enrichment does **not** itself produce a new `interaction_id`, so you cannot chain a further follow-up off of an enrichment.

**IMPORTANT:** Always include `--no-wait` so the command returns immediately instead of blocking.

Parse the `--json` output to extract `taskgroup_id` and `url`. The output is `{taskgroup_id, url, num_runs}` — there is no `interaction_id` field, do not look for one. Immediately tell the user:

- Enrichment has been kicked off
- The monitoring URL where they can track progress

Tell them they can background the polling step to continue working while it runs.

## Step 2: Poll for results

Pick a concrete output path (e.g., `/tmp/enrichment-acme.json`). Note: the file is JSON regardless of the extension you choose — it's an array of `{input, output}` objects, not a CSV. Name it `.json` to avoid confusing yourself or the user.

```bash
parallel-cli enrich poll "$TASKGROUP_ID" --timeout 540 --output "/tmp/enrichment-<descriptive-name>.json"
```

Important:

- Use `--timeout 540` (9 minutes) to stay within tool execution limits
- The `--target` from step 1 is unused in `--no-wait` mode — only `--output` here determines where results are saved, and the file is always JSON

### If the poll times out

Enrichment of large datasets can take longer than 9 minutes. If the poll exits without completing:

1. Tell the user the enrichment is still running server-side
2. Re-run the same `parallel-cli enrich poll` command to continue waiting

## Response format

**After step 1:** Share the monitoring URL (for tracking progress).

**After step 2:**

1. Report number of rows enriched
2. Preview first few rows from the output file (it's a JSON array of `{input, output}` objects)
3. Tell the user the full path to the output file

Do NOT re-share the monitoring URL after completion — the results are in the output file.

## Setup

If `parallel-cli` is not found, install and authenticate:

```bash
/parallel:parallel-cli-setup
```

If any `parallel-cli enrich` command returns `403`, tell the user balance is likely required. Offer to run `parallel-cli balance get`, and if needed ask for explicit confirmation before running `parallel-cli balance add <amount_cents>`. Then retry the original enrichment command.
