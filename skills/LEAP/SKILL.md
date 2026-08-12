---
name: LEAP
description: |
  LEAP builds skills through two pipelines: Branch A distills a skill from raw
  data, while Branch B combines multiple skills into one. It is called by the
  main SkillAlchemy workflow. Use when SkillAlchemy requires distillation or fusion.
---

# LEAP · Skill Builder

LEAP does not choose the request type or interact with the user. SkillAlchemy
selects the branch and handles each user checkpoint. LEAP runs the selected
pipeline and returns the result.

## Branch Routing

| Command | Branch | Pipeline |
|---------|--------|----------|
| `distill` / `distillation` | **Branch A** | Distillation pipeline — extract the target OS from raw data and compile it into a persona/tool skill |
| `fuse` / `fusion` | **Branch B** | Fusion pipeline — method.skill (skeleton) × subject.skill(s) (flesh) → output.skill |

## Invocation Modes

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Full run** | No special keyword | Run the full pipeline and output a skill package |
| **Plan only** | `stop after Stage 3` or `stop_after_stage: 3` | Run Branch A Stages 1-3 only; stop after writing `research_plan.json` |
| **Resume** | `continue from Stage 4` or `resume_from_stage: 4` | Skip Branch A Stages 1-3; use the existing `research_plan.json` and run Stages 4-7 plus Gate 1 |

---

# Branch A: Distillation Pipeline

```text
Source Intake → Intake Assessment → Research Plan Design
  → Research Swarm → Gate 1: Merge
  → Exemplar Discovery → Synthesis (3 agents)
  → Skill Compilation
```

Core principle: extract the operating system behind the source, not just the content or answer.

---

## A-Stage 1: Source Intake

Input: person, author, method, organization, domain, URL, repo, or local files.

Create package workspace at `output/<target-slug>-skill/`:

```
output/<target-slug>-skill/
├── README.md
├── SKILL.md.draft
├── references/             # agent reports + exemplars
├── intermediate/           # structured data
└── examples/               # persona: required; tool: optional
```
> Do not pre-create `templates/`; output templates live in LEAP's shared layer and
> are not needed in the generated skill.

Write `intermediate/open_world_task.json` with the capability brief `g`, target,
source-access specification `S` (allowed source types, retrieval channels, and
exclusions), execution/package constraints `C`, and `depth_level`. Every later
retrieval must comply with `S`; existing skills are not eligible exemplars unless
`S` explicitly permits them.

| `depth_level` | Effect | Use case |
|:--|:--|:--|
| `quick` | Agent count ≤3 | Rapid prototype |
| `standard` | No correction to auto-assessment | Daily use (default) |
| `deep` | Agent count upper bound +1, capped at 8 | Broader evidence coverage |

---

## A-Stage 2: Intake Assessment

### Step 1: Source Modality Analysis

Classify every source by what it can reveal:

| Modality | Examples | Reveals |
|----------|---------|---------|
| `transcript_interview` | podcasts, video captions, Q&A | spontaneous reasoning, analogies, changed positions |
| `longform_text` | books, papers, essays, newsletters | core arguments, methodology, narrative structure |
| `secondary_criticism` | reviews, biographies, analysis | external perspective, blind spots, competing views |
| `video_subtitle` | YouTube, Bilibili captions | speech patterns, unscripted reasoning |
| `social_media` | posts, threads | expression patterns, real-time reactions |
| `code_repo` | git repos, PRs | architecture patterns, API contracts, testing strategy |

For each modality present, note what operations it could reveal. Skip absent ones.

### Step 2: Domain Inference

Read `domains/<domain>/domain.md` to confirm. Record primary + secondary domains.

### Step 3: Evidence Depth Assessment

**Don't count sources — assess their density.**

- ≥3 high-density sources across ≥2 modalities → **rich** (5-8 agents)
- 1-2 high-density sources → **moderate** (3-5 agents)
- 0 high-density, all medium/low → **sparse** (2-3 agents)

Apply `depth_level` correction: quick→floor+cap at 3, standard→no change,
deep→ceiling+1, cap at 8.

### Step 4: Skill Mode Determination

| Target type | Skill mode | Behavior |
|-------------|-----------|----------|
| Person / author / expert | `persona` | First-person role-play. Includes Role-Playing Rules, Identity, How I Speak, and Decision Heuristics |
| Domain / method / organization | `tool` | Third-person analytical. Has Activation Rules, Agentic Protocol, Operation Models |

---

## A-Stage 3: Research Plan Design

### How to select candidate operational factors

1. Start from Lens's candidate operational factors and acquisition targets. Hidden
   dimensions, brief-specific values, and matched contrastive tests are one planning
   mechanism, not separate discovery stages.
2. Read primary domain pack: `domains/<primary-domain>/domain.md` → candidate factors
3. **If persona, also read `domains/persona-os/domain.md`.** This cross-cutting layer
   provides OS extraction lenses (decision under constraint, failure processing,
   value conflict resolution, attention allocation, etc.).
4. Cross factors with source modality: match → active, no match → skip
5. Apply evidence depth cap: sparse→merge, moderate→1:1, rich→split
6. Derive a new candidate factor only when the source exposes a behavior-relevant
   distinction not already represented.

For each active factor `d`, retain or construct a paired acquisition target
`<d, x, x'>` whose contexts differ along `d`. Convert it into a focused research
question asking whether the contexts require different treatment in condition,
action, recovery, or verification. A factor is confirmed as an implicit requirement
only when acquired evidence supports such a treatment difference.

### Self-Check Before Writing research_plan.json

1. **Depth match** — Does agent_count fall within the depth range?
2. **Modality coverage** — Are source_modalities_used actually present?
3. **Factor coverage** — Does every active factor have a matched acquisition target?
4. **Merge intent** — Deliberate or lazy? Document the rationale.

### Search direction must target dilemmas

```
Good: "What was the hardest decision at [event]? What options did they have?"
Bad:  "What is their leadership style?"
```

Every agent's search_direction should name a specific moment, event, or decision
that can be traced to a verifiable source.

Write `intermediate/research_plan.json` with one record per planned research agent.
Each record must include the candidate factor `d`, matched contexts `x` and `x'`,
the focused research question, the procedural components to compare, permitted
source types and retrieval channels inherited from `S`, and the assigned search
direction. Together these focused questions form `Q`.

### Plan-Only Mode Stop Point

**If invoked with `stop after Stage 3` or `stop_after_stage: 3`:**

Stop immediately after writing `research_plan.json`. Output:

```
Research plan generated and saved to intermediate/research_plan.json.

[N] agents, dimensions:
  R1 — [dimension]: [search_direction summary]
  R2 — [dimension]: [search_direction summary]
  ...
```

Do not enter Stage 4. Wait for Skill-Alchemy to return a confirmation or an
adjusted instruction.

---

## A-Stage 4: Research Swarm

**Resume mode:** If invoked with `continue from Stage 4`, read the agent
configuration directly from the existing `intermediate/research_plan.json`.
Skip Stages 1-3.

Launch N agents in parallel. Each agent writes `references/R<NN>-<agent_id>.md`:

```
Status: pass (or warning / fail)

## Structured Findings
  - Finding ID: stable identifier used by later artifacts
  - Acquisition Target: `<factor, x, x'>`
  - Context x: seed operating conditions
  - Treatment in x: source-grounded behavior, not an executable instruction
  - Evidence for x: source_id, type, confidence, and source-stated boundary
  - Context x': matched conditions with only the target factor changed
  - Treatment in x': source-grounded behavior, not an executable instruction
  - Evidence for x': source_id, type, confidence, and source-stated boundary
  - Affected Components: condition / action / recovery / verification
  - Relation: changed / invariant / unresolved
## Dilemma Decision Cases (≥2 required)
  ### Case N: [one-line summary]
  - Dilemma: specific conflict or hard choice
  - Constraints: what limited their options
  - Decision Steps: what they did, step by step
  - Outcome: what happened
  - Extractable Operation: generalizable rule/pattern/heuristic
## Evidence Sources (source_id, type, confidence)
## Supported Candidate Operations
## Rejected or Weak Candidate Operations
## Target-specific Patterns
## Boundaries and Uncertainties
## Recommendations for Later Skill Compilation
```

**Agent Contract:** Every report begins with `Status: pass` / `warning` / `fail`.
Dilemma Decision Cases are the most important section for persona targets —
they are the raw material from which mental models and heuristics are built.

**Agent Timeout Rule:** If any research agent hasn't produced a report within
10 minutes, do not wait. Proceed with completed agents. Gate 1 checks:
- Persona: ≥4 total Dilemma Cases across all completed reports → pass.
  <4 → downgrade depth to quick and relaunch with fewer (≤2) agents.
- Tool: ≥2 total Dilemma Cases → pass. <2 → same downgrade.
- Mark missing agents in `merge_report.json`: `"agents_lost": ["R2", "R3"]`.

---

## A-Gate 1: Research Merge

Agent uses `data-analysis` skill to process reports:

1. Read all R1-Rn reports
2. Extract Status + all sections
3. **Dilemma Case gate**: persona targets — per-report 0 cases = warning,
   combined total <4 = fail
4. Normalize every paired finding into `evidence_matrix.json`, retaining both
   contexts, both treatments, affected components, boundaries, and evidence IDs.
5. Write one entry per acquisition target to `contrast_records.json`:
   - `changed`: evidence supports different treatment in at least one component;
     a source-stated applicability boundary along the target factor is sufficient
     evidence that the bounded component changes across the matched contexts;
   - `invariant`: evidence supports the same treatment across non-equivalent contexts;
   - `unresolved`: either side lacks enough evidence or the comparison conflicts.
     Missing evidence for only one context must not by itself be labeled `changed`.
   Use this schema:

   ```json
   {
     "factor": "d",
     "context_x": "seed context",
     "context_x_prime": "matched context with d changed",
     "component_relations": {
       "condition": "changed",
       "action": "invariant",
       "recovery": "unresolved",
       "verification": "invariant"
     },
     "evidence_x": ["F01"],
     "evidence_x_prime": ["F02"],
     "overall_relation": "changed",
     "confirmed_implicit_requirement": true,
     "evidence_stated_boundary": "..."
   }
   ```
6. Confirm a factor as an implicit requirement only when its contrast record is
   `changed`. Keep `invariant` and `unresolved` records for later scope decisions.
7. Detect cross-report contradictions and write `contradiction_report.json` and
   `merge-summary.md`.
8. Write `merge_report.json`, `evidence_matrix.json`, and `contrast_records.json`.

Gate 1 merges and checks research evidence only. It must not induce candidate
procedures or make General/Scoped/Exclude decisions.

---

## A-Stage 5: Exemplar Discovery

Retrieve the best exemplars in real time from the public skill pool on skills.sh,
then inject them into Compilation as few-shot structural references.

### Retrieval Workflow

This stage runs only when existing skills are an allowed source type under `S`.
Otherwise record `status: "not_permitted"` and continue without exemplars.

1. **Search with find-skills:**
   Call the skills.sh find-skills interface with keywords for the target. Return
   the top 20 candidate `skill_key` values.

2. **Download candidate SKILL.md files concurrently and score them mechanically:**
   - Download the SKILL.md files for all 20 candidates concurrently from GitHub raw.
   - Run `python3 scripts/score_skill.py --skill <path> --json` for each candidate.
   - Sort by `quality_score`: prioritize elite candidates (≥11) and discard drafts (<9).

3. **Select and inject the best candidates automatically:**
   - Take the top 3-5 elite exemplars, prioritizing scores ≥11.
   - Write them to `references/exemplars/exemplar-<N>.md`.
   - Write the scoring results to `references/exemplar_candidates.json` for audit.

4. **Handle cases with no qualified result:**
   - If every candidate scores below 9, broaden the search terms and search once more.
   - If no elite candidate is found after two rounds, set `status: "degraded"` in
     `exemplar_discovery.json`.
   - **You must still attempt to obtain at least one exemplar.** It is the basis
     for compilation quality.

---

## A-Stage 6: Synthesis

Run the following steps in order. Stage 6 is the only stage that may induce
candidate procedures or make admission decisions.

### S1: Decision Alignment

Group findings by the procedural decision they inform, not by source topic. Write
`operation_candidates.json`. Each candidate must have this shape:

```json
{
  "candidate_id": "P01",
  "decision": "the procedural decision being made",
  "condition": {"content": "...", "evidence_ids": ["F01"]},
  "action": {"content": "...", "evidence_ids": ["F01", "F03"]},
  "recovery": {"content": null, "evidence_ids": []},
  "verification": {"content": "...", "evidence_ids": ["F04"]}
}
```

Leave an unsupported component empty. Synonymous source terms may be normalized,
but named entities and fixed choices must not be generalized unless a broad source
statement or invariant evidence across non-equivalent contexts supports doing so.
When distinct treatments are supported under different recorded conditions, preserve
them as separate conditional cases. Do not collapse them into one rule. Incompatible
treatments under matched conditions remain unresolved conflicts.

### S2: Procedure Admission

For each candidate, write an entry to `admission_records.json`:

```json
{
  "candidate_id": "P01",
  "F_plus": ["F01", "F03", "F04"],
  "F_minus": [],
  "sigma": "widest operating scope supported by the listed evidence",
  "supported": true,
  "consistent": true,
  "reusable": true,
  "reuse_basis": "broad_source_statement | cross_context_invariance | none",
  "decision": "General",
  "rationale": "short evidence-based explanation"
}
```

Apply these rules exactly:

1. `supported=true` only when every populated component is backed by evidence that
   applies within `sigma`.
2. `consistent=true` only when no `F_minus` evidence prescribes incompatible
   treatment under overlapping conditions within `sigma`.
3. Restrict `sigma` before classification when support holds only in a narrower scope.
4. `reusable=true` only when an allowed source explicitly states broader
   applicability or invariant evidence supports the same treatment across at least
   two non-equivalent contexts. A single source-local case is not reusable.
5. Classify as `General` when supported, consistent, and reusable; `Scoped` when
   supported and consistent but not reusable; otherwise `Exclude`.

Write `admitted_general.json`, `admitted_scoped.json`, and
`excluded_candidates.json` from these records. Excluded candidates remain in the
audit trail and must not be passed to compilation.

### S3: Package Design

Write `package_plan.json`. Map only admitted General and Scoped content to an
executable organization under `C`. Do not create procedures, fill unsupported
components, or change admitted scope.

---

## A-Stage 7: Skill Compilation

Compile final package from all research + synthesis reports + exemplars.

### Compilation Inputs (in Priority Order)

1. `admitted_general.json` — the only source of reusable instructions.
2. `admitted_scoped.json` — the only source of context-bound examples or notes.
3. Execution and packaging constraints `C` from `open_world_task.json`.
4. **`skill-grammar.md` — MUST be read before rendering.** Use its patterns to
   organize the package, place package-relative references, apply progressive
   disclosure, and avoid known anti-patterns.
5. Permitted exemplars, when available, may guide organization and presentation only.

Compilation must not create a new procedure, fill an unsupported component, promote
an excluded candidate, or broaden admitted scope. Domain packs, research reports,
and exemplars are audit or presentation aids; they are not additional sources of
skill instructions at this stage.

### Package contents

```
<skill-name>/
├── SKILL.md                   # lean entry point — runtime loaded
├── skill.json                 # metadata (name, version, skill_mode, domain)
├── README.md                  # storefront (see template in shared layer)
├── references/
│   ├── sop_models.md          # full operation model cards (runtime on-demand)
│   └── research_notes.md      # human-readable evidence summary
├── scripts/                   # optional executable routines used by the skill
├── assets/                    # optional templates or static resources
├── examples/
│   └── demo_conversation.md   # persona: 3-4 scenarios (required)
└── intermediate/              # pipeline audit trail
```

Create `scripts/`, `assets/`, and `examples/` only when the admitted content and `C`
require them. Every optional resource must be referenced through a package-relative
path from `SKILL.md` or another reachable package file.

> Runtime loads only SKILL.md. The runtime protocol reads `sop_models.md` on demand.
> R1-Rn and `intermediate/` are audit artifacts.

**A persona MUST include `examples/demo_conversation.md` with 3-4 scenarios:
common, edge case, and refusal. Missing file → fail.**
The `examples/` directory is optional for tool mode.

### Post-Compilation Cleanup

After compilation, delete temporary artifacts to keep the output clean:

1. Delete `references/exemplar_candidates.json`—the temporary scoring file has
   already served its purpose.
2. Delete `references/exemplars/`—the intermediate reference copies have already
   served their purpose.
3. Delete empty directories.
4. Keep `references/R*.md` as research evidence, `intermediate/` as the audit
   trail, and the output package.

# Branch B: Fusion Pipeline

```text
method.skill (skeleton) × subject.skill(s) (flesh) → output.skill
```

WEAVE is not a concatenator. If you can tell where one skill ends and
another begins, the weave failed.

---

## B-Step 1: Retrieve Skills

Confirm that every skill required for fusion is ready:

```
primary: "Interview Techniques"       ← workflow skeleton
secondary: ["BeiDou Navigation"]      ← style/persona source
depth: "standard"
```

Retrieve each required skill in this order:

1. Local `output/` directory (skills generated previously)
2. Installed skills (`~/.claude/skills/`)
3. **find-skills online search** (semantic search over the public skills.sh pool)
4. GitHub raw download

If a skill does not exist:
- Tell the user which skill must be generated first and recommend Branch A distillation.
- Or ask the user to provide the path to an existing skill.

After retrieving a skill, run
`python3 scripts/score_skill.py --skill <path> --json` to verify its quality.
A draft skill scoring below 9 should not be used as a fusion source—garbage in,
garbage out.

**When find-skills returns candidates, write the scoring results to
`references/fusion_candidates.json`:**
```json
[
  {"skill_key": "xxx", "score": 12, "summary": "...", "recommended_role": "primary"},
  {"skill_key": "yyy", "score": 9, "summary": "...", "recommended_role": "secondary"}
]
```
Skill-Alchemy presents these candidates to the user for confirmation. LEAP does
not handle the interaction itself.

---

## B-Step 2: Parse

### 2.1 Parse primary skill (skeleton)

Extract:
- **Workflow**: every step, in order. Number them.
- **Output format**: what the skill produces at each step
- **Decision points**: if-then branches, conditional logic
- **Constraints**: what this skill cannot/will not do

The primary skill determines the **structure** of the output.

### 2.2 Parse secondary skill(s) (flesh)

For each secondary skill, extract:
- **Role/persona**: how they speak, their identity, their worldview (persona)
  OR their domain lens, their operation models (tool)
- **Style elements**: tone, rhythm, vocabulary, forbidden phrases, signature patterns
- **Heuristics/decision rules**: their falsifiable operating rules
- **Constraints**: what this skill cannot/will not do
- **Evidence anchors**: verifiable sources that back their patterns

The secondary skills determine the **texture** of the output.

---

## B-Step 3: Weave

Fusion depth is controlled by `depth_level`.

### quick — Style Injection

Each style element from secondary skills is injected into the primary
workflow at the most relevant step. Minimal rewriting.

```
Interview Techniques Step 3 "Generate Core Questions"
  → Inject BeiDou Navigation's questioning style: begin with a specific
    experience, establish rapport, and then probe further
```

### standard — Structured Weave (default)

1. **Rewrite the role.** Create a new unified identity.
   - Bad: "You are BeiDou Navigation. You are an interviewer."
   - Good: "You are a BeiDou Navigation-style interview-planning assistant. You
     learn and reuse his interview methods without claiming to be him."

2. **Weave workflow × style.** For each step in the primary workflow,
   embed relevant style/pattern from secondary skills.
   - Each style injection must cite its source skill section.
   - No step should feel "unstyled" — every step gets at least one texture element.

3. **Merge constraints.** Union of all source skill constraints.
   Remove duplicates. Flag conflicts (if primary says "do X" and secondary
   says "never do X").

4. **Check for gaps.** Are there steps in the workflow that no secondary
   skill has pattern coverage for? Mark them as `[General Pattern]`—filled by
   general best practices, not specific to any source.

### deep — Weave + Gap Resolution

Same as standard, plus:
1. **Detect conflicts.** When two source skills contradict on a point,
   resolve explicitly. Default: primary skill wins on workflow decisions,
   secondary skill wins on style decisions. Document every conflict and resolution.

2. **Fill gaps.** For steps marked `[General Pattern]`, launch a lightweight
   research agent to find domain-specific patterns.

3. **Source traceability.** Verify that every style claim in the output can
   be traced back to a specific section of a source skill. Verify that no
   constraint was dropped.

---

## B-Step 4: Output

Generate `output.skill` using the SKILL.md templates in the shared layer below.

### Role naming convention
- "BeiDou Navigation-style Interview-Planning Assistant"—"style" indicates
  derivation rather than identity.
- "Decision Framework Based on Zhang Yiming's Product Philosophy"—"based on"
  indicates the source.

### Package contents

```
<skill-name>/
├── SKILL.md                   # lean entry point — runtime loaded
├── skill.json                 # metadata (name, version, skill_mode, source_skills)
├── README.md                  # storefront (see shared layer)
├── references/
│   └── sop_models.md          # full operation model cards (runtime on-demand)
└── examples/
    └── demo_conversation.md   # persona: 3-4 scenarios (required)
```

### Post-Compilation Cleanup

Same as Branch A:
1. Delete `references/fusion_candidates.json` (temporary scoring file).
2. Delete all intermediate reference files, including temporary exemplar copies.
3. Delete empty directories.
4. Keep `references/` as the audit trail.

---

# Shared Layer

Branches A and B share the following templates and infrastructure.

## SKILL.md Output Templates

### Tool Mode (`skill_mode: "tool"`) — 7 Required Sections

```
## Activation Rules
Concrete examples of both triggering and non-triggering requests. List 4-5
scenarios in each category.

## Agentic Protocol
Executable steps. Write "do X, then Y," not "consider X":
Step 1: Determine the stage
Step 2: Match the model (read sop_models.md)
Step 3: Execute the diagnosis
Step 4: Produce the output (select an output mode)

## Core Operation Models
H1-Hn summary table. Format:
| # | Model | Core proposition | Primary source |
|---|-------|------------------|----------------|
| H1 | **Model name** | One sentence | Source |
Full cards live in references/sop_models.md.

## Output Style
- Lead with a one-sentence conclusion, then expand. Do not paste an entire model card.
- Use natural paragraphs rather than Markdown tables unless the user explicitly
  asks for a comparison table.
- When citing a source, say "PG argued in a 2012 essay..." rather than "According
  to H1 in references/sop_models.md..."
- Forbidden phrases: "Analyzing this with the framework...", "Following the model
  card...", and "Let me analyze this systematically..."
- Stop after answering. Do not ask, "Would you like me to expand further?"

## Output Modes
| Mode | Trigger | Output structure |
|------|---------|------------------|
| ... | ... | ... |
Define 4-7 modes.

## Boundary Rules
Provide 7-8 numbered rules covering evidence boundaries, scope of application,
prohibited actions, and version cutoff.

## References
Pointer table: sop_models.md + research_notes.md + R reports + S reports.
```

### Persona Mode (`skill_mode: "persona"`) — 8 Required Sections + 1 Optional Section

```
## Role-Playing Rules (most important; place first)
Respond directly as [Person's name]. Speak in the first person.
The reader already knows who you are. Do not repeat your background in every turn.
Use my tone, rhythm, and vocabulary. When uncertain, hesitate in character.
If someone is clearly speaking with you for the first time, include a brief disclaimer.
Exit the role when the user says "exit role" or "switch back to normal."

## Identity
Write 3-5 first-person sentences. This is not a biography—it is a handshake.
Include only the facts most important for understanding how this person sees the world.

## How I See the World
Include 3-5 mental models, each in a paragraph of no more than 5 lines.
Use conversational paragraphs rather than structured cards. Write in this person's voice.
Put evidence and limitations in references/sop_models.md rather than inline.

## How I Speak
The first sentence is the strongest output-format constraint:
"I am [identity], not [contrasting identity]. Do not answer with bullet points or
numbered lists."
Sentence patterns (length, question-to-answer ratio) · vocabulary (frequent,
forbidden) · rhythm (conclusion first / context first)
Humor (self-deprecating / sarcastic / absurdist / none) · certainty
(uncertain / self-evident)
"Things I Would Never Say" (2-3 sentences this person would never say; these
establish distinctiveness better than positive descriptions)
"My Signature Phrase" (one expression that makes the persona immediately recognizable)
Citation habits + taboos

## Decision Heuristics
Include 3-5 items. Format: rule name — one-sentence description + applicable
scenario. Every item must be falsifiable.
❌ "Think long-term" (not falsifiable)
✅ "If I cannot figure it out in three minutes, put it in the Too Hard pile"
(falsifiable)
Put evidence in references/sop_models.md rather than inline.

## Runtime Protocol
A 5-step SOP-driven process:
1. Match the model: read references/sop_models.md and scan "When to use" for a
   matching model card.
2. Act on the model: structure the response strictly according to the Action steps
   and cite the Evidence source.
3. Check boundaries: compare against the Boundary field, refuse honestly when out
   of bounds, and proactively avoid Failure modes.
4. Verify factual questions first: specific facts → WebSearch → analyze through
   the mental-model framework.
5. Answer experiential judgments directly: values or casual conversation → respond
   directly; beyond the persona's knowledge → "This is outside my expertise, so I
   will not pretend to know."

## Boundaries
Approximately 5 lines. State that the skill cannot represent the real person and
include an information cutoff date.
Final line: Depth: quick/standard/deep

## References
Pointers: references/sop_models.md + references/research_notes.md

## Values (optional)
Include only when the person has strong, distinctive, publicly documented values.
Do not use this section as filler.
```

**Every persona skill MUST include `examples/demo_conversation.md`** — 3-4
short conversation scenarios: a common ask, an edge case, a boundary refusal.

**Every persona skill MUST include a `README.md`** using this template:

```markdown
# [Person's name] · [English name or label]

> "[One verified quote that best represents this person]"

[One sentence: who they are, what they did, and why they are worth listening to.
No more than 30 words.]

## Installation
    cp -r [skill] ~/.claude/skills/[name]/

## Trigger Scenarios
[Describe 3-5 typical trigger scenarios in natural language.]

## Mental Models
| # | Model | One sentence |
|---|-------|--------------|
| 1 | [Name] | [15 words or fewer] |

## How They Would Say It
- **Signature phrase:** [One sentence]
- **Would never say:** [One sentence] / [One sentence] / [One sentence]

## Disclaimer
This simulated persona is distilled from public sources and does not represent
the real person's views. Information cutoff: [Month, Year].
```

README rules: top quote MUST be real and verified. Keep under 40 lines.
The Mental Models table must contain exactly the same models as How I See the World.
Signature phrase / Would never say must exactly match How I Speak.

### Forbidden in all modes

- Exact file paths from one benchmark instance
- Oracle/verifier logic
- Copied protected expression
- For persona: do not fabricate quotes, do not claim generated text IS the person's
- Progressive disclosure: SKILL.md is the lean entry point; detailed evidence in references/

---

## Shared Infrastructure

- `domains/` — 12 domain packs (11 primary domains + persona-os), used to select
  Branch A Stage 3 research dimensions.
- `references/skill-grammar.md` — skill-writing methodology derived from
  skills.sh data; required reading before Branch A/B compilation.
- `scripts/score_skill.py` — 13-point mechanical scoring for runtime quality
  filtering in A-Stage 5 / B-Step 1.
- `scripts/download_subtitles.sh` + `scripts/srt_to_transcript.py` — video-source
  processing, used as needed.
- `scripts/build_corpus.py` + `scripts/build_component_index.py` — data-mining
  tools used to build skill-grammar; required for open-source builds, not at runtime.
- `find-skills` (skills.sh) — online semantic skill retrieval and the candidate
  discovery layer for A-Stage 5 / B-Step 1.
