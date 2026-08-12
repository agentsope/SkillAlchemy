# Skill Grammar — How to Write a Good Skill

A writing methodology distilled from a large collection of public skills on
skills.sh. The Skill Compilation agent loads this file during compilation.

**Data validation:** Based on the real skills.sh corpus with quality-score filtering.

### Corpus Statistics Snapshot (Full Sample)

| Dimension | Finding |
|-----------|---------|
| Trigger pattern | keyword-match 75% / hybrid 16% / context-match 8% / explicit-call 1% |
| SOP type | chain-of-steps 71% / template-fill 22% / reference 7% |
| Length | <100 lines 27% / 100-300 lines 45% / 300-800 lines 26% / 800+ lines 1% |
| Description includes trigger | 59% yes / 41% no ⚠️ |

### Quality-Weighted Snapshot (Top 60%, 111 Skills, Score ≥9/13)

| Dimension | All | Top 60% | Change |
|-----------|-----|---------|--------|
| keyword-match | 75% | 77% | → |
| hybrid trigger | 16% | **21%** | ↑ High-quality skills use hybrid triggers more often |
| context-match | 8% | **2%** | ↓↓ Pure context triggering is a weak signal |
| chain-of-steps | 71% | **79%** | ↑ Concrete steps correlate with quality |
| reference type | 7% | **1%** | ↓↓↓ Pure reference skills are almost always low quality |
| <100 lines | 27% | **9%** | ↓↓↓ Quality filtering removes many skills that are too thin |
| 100-300 lines | 45% | **54%** | ↑ Best length range |
| 300-800 lines | 26% | **37%** | ↑ High-quality skills are longer on average |

### Pattern Associations in Good Skills (Frequent Co-Occurrence in the Top 60%)

| Associated patterns | Frequency | Interpretation |
|---------------------|:---------:|----------------|
| chain-of-steps + diagnostic | 74% | Good skills use step chains for diagnosis |
| keyword-match + chain-of-steps | 63% | Winning combination: keyword triggers + stepwise execution |
| chain-of-steps + validation | 56% | Diagnosis must be followed by validation |
| chain-of-steps + generation | 46% | Stepwise generation is the second most common pattern |
| chain-of-steps + comparison | 37% | |

---

## 1. SKILL.md Format

### Frontmatter (YAML)

```yaml
---
name: skill-name                    # 1-64 characters: lowercase letters, digits, and hyphens
description: >-                     # 1-1024 characters: function + trigger conditions
  What this skill does. When to use it.
---
```

**The description is the only trigger mechanism.** It must include both:
- A functional description (what the skill does)
- Trigger conditions (when to use it)

```
✅ Good: "Extracts text and tables from PDF files, fills PDF forms, and merges
       multiple PDFs. Use when working with PDF documents or when the user
       mentions PDFs, forms, or document extraction."

❌ Bad: "Helps with PDFs."
```

### Markdown Body

The SKILL.md body loads when the skill is triggered. Recommended: <5,000 tokens.

---

## 2. Trigger Patterns (5 Types)

### 2.1 keyword-match
The most common pattern. It triggers when the user says specific words in a conversation.
- **How to write it:** Put 3-6 trigger keywords in the description.
- **Best for:** Tool skills and domain-knowledge skills.
- **Example:** `security-audit` → "Use when security audit, vulnerability scan, OWASP, dependency check"

### 2.2 context-match
Triggers automatically based on the working directory or file type.
- **How to write it:** Describe contextual conditions in the description.
- **Best for:** Project-level skills (Docker, Git, CI/CD).
- **Example:** `docker-development` → "Use when working with Dockerfiles, docker-compose, or containerization"

### 2.3 explicit-call
The user explicitly invokes `/skill-name` or `@skill-name`.
- **How to write it:** The name is the trigger; the description explains the function.
- **Best for:** Skills that require explicit intent, such as high-risk operations.
- **Example:** `security-review` → the user explicitly says "security review"

### 2.4 hybrid
Combines keyword and context. The description includes both keywords and context.
- **How to write it:** State keywords first, then the scenario.
- **Best for:** Complex trigger conditions.
- **Example:** `deploy-check` → "Use before git push when deploy, release, or production is mentioned"

### 2.5 always-on
Loads in every conversation. Used for meta-skills or rule injection.
- **How to write it:** Make the description very broad or designate it as agent-rules.
- **Best for:** AGENTS.md generation and global rules.
- **Warning:** Easy to misuse; use only when it is genuinely needed every time.

---

## 3. SOP Templates (4 Types)

### 3.1 chain-of-steps
Execute steps sequentially: Step 1→2→3→4→5.
```
## Instructions
### Step 1: [Action]
What to do, which tool to use, and what output to expect.

### Step 2: [Action]
...
```
- **Best for:** Pipeline operations such as PDF processing, data cleaning, and deployment.
- **Key rules:**
  - Every step has a verifiable output.
  - Dependencies between steps are explicit.
  - Failure paths specify which step to jump to.

### 3.2 model-card-driven
Give each concept an operation card, read on demand at runtime.
```
## Core Models

| # | Model | When to Use | Key Action |
|---|-------|-------------|------------|
| H1 | **Model name** | Trigger condition | Core operation |

Full cards in `references/sop_models.md`.
```
- **Best for:** Complex decision skills with multiple independent concepts or frameworks.
- **Key rules:**
  - Every card has 8 fields: When-to-use / Inputs / Action / Output / Evidence / Failure Mode / Boundary / Confidence.
  - SKILL.md contains only the summary table; cards live in `references/`.
  - Runtime Protocol Step 1 reads `sop_models.md` to match a model.

### 3.3 decision-tree
An if-then branching structure that selects a path based on user input.
```
## Decision Flow

1. Does the user have [condition A]?
   → Yes: Go to [path A]
   → No: Continue to 2.

2. Is [condition B] present?
   → Yes: [action B]
   → No: [default action]
```
- **Best for:** Diagnostic skills such as bug investigation, security audits, and code review.
- **Key rules:**
  - Every branch has an explicit decision condition.
  - Each leaf node is a concrete action, not another decision.
  - Include a default/fallback branch.

### 3.4 template-fill
The user provides information, and the skill fills a template.
```
## How to Use

1. Collect: [field1], [field2], [field3]
2. Validate: check [field1] against [rule]
3. Fill: insert into template at `templates/[name].md`
4. Output: rendered [output_type]
```
- **Best for:** Document generation, report completion, and PR templates.
- **Key rules:**
  - Clearly distinguish required and optional fields.
  - Give every field a validation rule.
  - State the template path explicitly.

---

## 4. Output Constraints (5 Types)

### 4.1 analysis-report
Lead with the conclusion, then expand in natural paragraphs.
```
Lead with a one-sentence conclusion, then expand.
Do not paste the entire model card.
```
- **Forbidden phrases:** "Analyzing this with the framework...", "Following the
  model card...", and "Let me analyze this systematically..."
- **Stop after answering.** Do not ask, "Would you like me to expand further?"

### 4.2 executable-code
Code block + brief explanation.
```
Code first, explanation after.
One code block per step.
```

### 4.3 conversational
First-person dialogue for persona mode.
```
Do not use bullet points or numbered lists.
The first sentence is the answer, not "Let me analyze this."
```

### 4.4 checklist-verify
Check each item and mark it pass/fail.
```
## Verification Checklist
- [ ] Item 1 — check X against Y
- [ ] Item 2 — verify Z is present
```

### 4.5 mixed
Switch output modes based on the question type. Requires an `## Output Modes` table.

---

## 5. Boundary Patterns (6 Types)

### 5.1 source-bound
Restrict information sources.
```
Use only public documentation, official repositories, or specified sources.
Do not cite unverified forum posts.
```

### 5.2 version-bound
Set a version or time cutoff.
```
Information cutoff: May 2026. Later version changes are not covered.
```

### 5.3 capability-bound
State explicitly what the skill can and cannot do.
```
Can: analyze SQL query performance. Cannot: modify a production database.
```

### 5.4 scope-bound
Restrict the applicable domain.
```
Applicable to web application security audits. Not applicable to mobile or IoT.
```

### 5.5 legal-bound
Provide a disclaimer or compliance statement.
```
This is not legal advice. It is for reference only and requires verification by
a professional auditor.
```

### 5.6 confidence-bound
Label uncertainty.
```
High confidence: based on official documentation. Low confidence: based on
community discussion and requires verification.
```

---

## 6. Persona Mode

### 6.1 Required Sections (8)

| # | Section | Purpose | Suggested lines |
|---|---------|---------|:---------------:|
| 1 | `## Role-Playing Rules` | Strongest output-format constraint | 6-10 |
| 2 | `## Identity` | A 3-5 sentence first-person handshake | 3-5 |
| 3 | `## How I See the World` | 3-5 mental models, each ≤5 lines | 15-25 |
| 4 | `## How I Speak` | Sentence patterns, vocabulary, rhythm, humor, certainty, forbidden phrases, and signature phrase | 10-15 |
| 5 | `## Decision Heuristics` | 3-5 if-X-then-Y rules | 5-10 |
| 6 | `## Runtime Protocol` | A 5-step SOP-driven process | 15-20 |
| 7 | `## Boundaries` | ~5 lines; cannot represent the real person | 4-6 |
| 8 | `## References` | Pointers to sop_models.md + research_notes.md | 1-2 |

### 6.2 "Things I Would Never Say" — The Key to Distinctiveness

This establishes distinctiveness better than positive descriptions. Include 2-3
sentences the person would never say.

```
✅ Good:
Munger would never say, "In my experience." He would say, "I have seen too many
people fail at this."
Jobs would never say, "That direction also has merit." He would say, "This is
shit," or, "This is amazing."

❌ Bad:
"I would not say anything unprofessional." This is too generic to be distinctive.
```

### 6.3 "My Signature Phrase" — Immediately Recognizable

Place one signature expression at the end of How I Speak.

```
Feynman: "If you cannot explain it clearly to a first-year student, you do not
really understand it."
Jobs: "Stop. The question itself is wrong."
```

### 6.4 Decision Heuristics — Falsifiable

Every rule must be falsifiable.

```
❌ Invalid: "Think long-term." → Not falsifiable; it applies to every situation.
✅ Valid: "If a problem cannot be figured out in three minutes, put it in the
Too Hard pile and skip it." → Falsifiable.
```

---

## 7. Tool Mode

### 7.1 Required Sections (7)

| # | Section | Key requirement |
|---|---------|-----------------|
| 1 | `## Activation Rules` | 4-5 concrete triggering and non-triggering examples each |
| 2 | `## Agentic Protocol` | Executable steps: "do X, then Y," not "consider X" |
| 3 | `## Core Operation Models` | H1-Hn + M1-Mn summary tables; full cards in `references/` |
| 4 | `## Output Style` | Conclusion first, forbidden-phrase list, no Markdown tables |
| 5 | `## Output Modes` | A table defining 4-7 modes |
| 6 | `## Boundary Rules` | 7-8 rules |
| 7 | `## References` | Pointer table |

### 7.2 Forbidden Output-Style Phrases

The most common tool-mode mistake is boilerplate language.

```
Forbidden phrases:
- "Analyzing this with the framework..."
- "Following the model card..."
- "Let me analyze this systematically..."
- "Would you like me to expand further?"

When citing a source, say, "PG argued in a 2012 essay..."
Do not say, "According to the H1 model card in references/sop_models.md..."
```

---

## 8. Anti-Pattern Checklist (9 Items)

| # | Anti-pattern | Consequence | Correction |
|---|--------------|-------------|------------|
| 1 | Trigger conditions are too broad | False triggers; activates in every conversation | Narrow the keywords and add contextual constraints |
| 2 | Description states function but not trigger | The skill is never invoked | Add "Use when..." |
| 3 | No boundary declaration | User expectations become uncontrolled | Add Boundary Rules / Boundaries |
| 4 | SOP is too vague ("consider X") | Not executable | Change it to "do X, then Y" |
| 5 | SKILL.md is too long (>8,000 tokens) | Loads on every trigger and wastes context | Move content into `references/` |
| 6 | References nonexistent files | Runtime read fails | Confirm every path exists |
| 7 | Fabricated quotations (persona) | Loss of credibility | Quote only publicly verifiable statements |
| 8 | **Pure reference skill** (no concrete steps) | Data: reference skills are only 1% of good skills and are concentrated among poor skills. A skill without executable steps is almost useless | Convert it to chain-of-steps or model-card-driven |
| 9 | **Too thin at <100 lines** | Data: <100-line skills are only 9% of good skills and are concentrated among poor skills (27%→9%) | Use at least 100 lines; target 100-300 |

---

## 9. Data-Backed Quality Signals

Based on quality-score analysis of a large skill corpus (≥9/13 = good), the
following are quantified characteristics of good skills:

### If You Can Do Only Three Things

1. **Write concrete steps, not reference documentation.** chain-of-steps appears
   in 79% of good skills versus 71% overall; reference skills nearly disappear
   among good skills (7%→1%).
2. **Use hybrid triggers, not context alone.** hybrid rises from 16% overall to
   21% among good skills, while context-match falls from 8% to 2%.
3. **Keep the skill between 100 and 800 lines.** Quality filtering removes many
   skills below 100 lines (27%→9%); 100-300 lines is the most reliable range
   (45%→54%).

### Winning Combination

The most common pattern combination among good skills in the top 60%:

```
keyword-match trigger
  + chain-of-steps SOP
  + diagnostic operation
  + validation operation
  + 100-300 lines
  + boundary declaration
```

This combination covers 63% of good skills.

### The 13-Point Quality Score

| Dimension | Points | Check |
|-----------|:------:|-------|
| Frontmatter has `name` | 1 | Basic |
| Frontmatter has `description` | 1 | Basic |
| Description includes trigger words | 2 | **Weighted**—without this, the skill will not be invoked |
| Description is specific (>80 characters) | 1 | |
| ≥3 sections | 1 | |
| Has boundary declaration | 2 | **Weighted**—core to managing user expectations |
| ≥5 concrete steps | 2 | **Weighted**—core to executability |
| Has an examples section | 1 | |
| Length is 100-400 lines | 1 | |
| Has a references/related section | 1 | |
| <30 lines (penalty) | -2 | Being too thin is a critical flaw |

**Threshold for a good skill: ≥9 points.** About 60% of the corpus qualifies.

---

## 10. Three-Tier Quality Pyramid

Based on quality-score analysis of a large skill corpus:

### Elite Tier (Top 10%, Score ≥11, 18 Skills)

**Characteristics with a 100% hit rate:**
- 100% use chain-of-steps, without exception.
- 100% have concrete steps (≥5 executable steps).
- 100% have a description with trigger wording and specific detail (>80 characters).
- 94% have boundary declarations.
- 89% include both diagnosis and validation.

**Elite template (ready to reuse):**

```
Trigger: keyword-match or hybrid
SOP: chain-of-steps
Operations: diagnosis + validation (both required)
Length: 200-350 lines
Required: boundary declaration + concrete steps + trigger description + multiple sections
Bonus: examples section + references section
```

**Elite skill examples:** `systematic-debugging`, `subagent-driven-development`,
`dispatching-parallel-agents`, `finishing-a-development-branch`, `seo-audit`,
`verification-before-completion`

### Middle Tier (Top 60%, Score ≥9, 111 Skills)

- 79% chain-of-steps, 20% template-fill
- hybrid triggers are 5 percentage points more common than in the full sample.
- 54% are 100-300 lines.

### Bottom Tier (Bottom 40%, Score <9, 75 Skills)

- Pure reference skills are concentrated almost entirely in this tier.
- Average length is 54 lines versus 273 lines for the elite tier, a 5× gap.
- Typical weaknesses: `too_thin` + `too_few_sections` + `description_too_vague`.

### One-Sentence Summary

> To write a good skill: chain-of-steps + diagnosis + validation + boundary
> declaration + 200-350 lines + a specific description with trigger wording.
> To write an elite skill, do all of the above and add examples and references.

---

## 11. Compilation Checklist

Apply this checklist while rendering the admitted content. It guides organization
and presentation; it is not a separate post-compilation validation stage and must
not introduce new procedures or broaden admitted scope.

### Structure
- [ ] Frontmatter includes `name` and `description`.
- [ ] Description includes function and trigger conditions.
- [ ] All required sections are present.
- [ ] SKILL.md body <5000 tokens

### Executability
- [ ] Every SOP step has a concrete action, not "consider X."
- [ ] Every step has a verifiable output.
- [ ] Runtime Protocol is executable (Read → match → act → verify).

### Distinctiveness (Persona)
- [ ] "Things I Would Never Say" contains 2-3 specific prohibited phrases.
- [ ] "My Signature Phrase" contains one phrase.
- [ ] Every Decision Heuristic is falsifiable.
- [ ] Persona is recognizable within 100 words.

### Boundaries
- [ ] Boundary declaration is clear about what the skill does and cannot do.
- [ ] Information cutoff date is present.
- [ ] Confidence is labeled.

### Evidence
- [ ] Key claims have sources.
- [ ] Citation style is natural; do not say, "According to H1 in references/sop_models.md."
- [ ] No fabricated quotations.
