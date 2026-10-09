# Quality rubric and evidence states

Use this guide to review the actual achieved artifact. The nine dimensions, state vocabulary and reporting convention are authored C06/C07, not an empirically validated numeric pass threshold. Admitted historical quality cases are preserved separately below. Read [quality checklist](../tests/quality-checklist.md) and [manual review](../tests/manual-review.md) when conducting review.

## Review protocol — authored C06/C07

1. Record which artifact exists: plan, source code, static result, preview, encoded file or a combination. Keep rights status independent.
2. For each acceptance criterion, record the actual observation method and covered region/time/frame/audio scope.
3. Apply the nine dimensions below only to evidence that can support them. Static parsing and stills do not establish continuous pacing, spoken intelligibility or audiovisual sync.
4. Record pass/fail/warning/not_executed/not_applicable/unknown explicitly. A required review that has not run remains not_executed; a missing necessary fact remains unknown.
5. Repair an observed failure using its matching admitted recovery or the explicit authored project requirement. Rerun the affected check and retain its updated scope.
6. Deliver artifact locations, remaining failures/gaps and the independent state report. Do not call the work a reviewed video because a command returned zero.

## Nine dimensions — authored C06

| Dimension | Review against the project | Evidence and limits |
|---|---|---|
| Narrative clarity | Audience/message, required events, factual claims and intended ending | Plan/script can be checked statically; viewer comprehension requires actual observation and is not inferred |
| Visual consistency | Declared project style, continuity, supplied brand constraints | Static tokens plus actual frames; no universal palette/type/style rule |
| Pacing | Declared shot/cue timing and experienced continuous rhythm | Timeline arithmetic verifies budget; continuous pacing requires full-motion viewing |
| Animation | Required motion, boundaries, continuity and seek/frame contract | Code checks plus consecutive frames; isolated stills omit between-frame behavior |
| Legibility | Literal copy, subject/caption overlap and observed visibility | Inspect actual rendered frames/time windows; module/film-local thresholds stay local |
| Factual accuracy | Supplied/sourced/unknown/synthetic labels, numerals, notes and formulas | Literal/source checks plus rendered factual-value inspection; do not invent proof |
| Audio | Intent, availability, track permissions, audible content and cue sync | Config/probe differs from actual listening; absent requested narration remains incomplete |
| Technical correctness | Actual file, dimensions, fps, duration, frame coverage and selected export path | Probe the encoded artifact; preview/build does not prove exported properties |
| Reproducibility | Exact engine/revision/dependencies/assets/rights and repeatability scope | Record actual repeated frames/runs/environment; no unexecuted reproducibility certification |

Do not average unknown or not_executed observations into a pass. If a project elects numeric scores or a pass threshold, record them as an authored package/project convention and state which required gates remain unresolved. No source-validated universal score is claimed.

## Independent state schema — authored C07

Each state has `status` from `pass | fail | warning | not_executed | not_applicable | unknown`, plus evidence and coverage. The keys describe separate facts; completion of one never automatically completes another.

```yaml
artifact_state:
  plan_available: {status: unknown, evidence: null, coverage: null}
  code_available: {status: unknown, evidence: null, coverage: null}
  static_checked: {status: not_executed, evidence: null, coverage: null}
  preview_observed: {status: not_executed, evidence: null, coverage: null}
  encoded_artifact_available: {status: unknown, evidence: null, coverage: null}
  technical_probe_passed: {status: not_executed, evidence: null, coverage: null}
  sample_frames_reviewed: {status: not_executed, evidence: null, coverage: null}
  full_motion_reviewed: {status: not_executed, evidence: null, coverage: null}
  audio_listened: {status: not_executed, evidence: null, coverage: null}
  rights_confirmed: {status: unknown, evidence: null, coverage: null}
  reproducibility_scope: {status: unknown, evidence: null, coverage: null}
```

Set audio listening to not_applicable only when the user/project intent is intentionally silent and that state is established. Narration intent with missing audio must not be labeled not_applicable. Sample coverage should identify actual timestamps/frame ranges; full-motion coverage must identify what was viewed; audio coverage must identify what was listened to. Reproducibility coverage identifies tested frames/runs, environment and dependencies rather than promising universal determinism.

## Evidence classes

- **Static:** source/schema/type/metadata checks. Supports only the properties actually checked.
- **Sampled frames:** actual images at identified times. Supports observed layout/content at those samples.
- **Consecutive frames:** actual boundary ranges. Can reveal local caption/transition defects within that range.
- **Full motion:** actual continuous viewing. Supports observed pacing/motion within its stated coverage.
- **Listening:** actual audible review. Supports observed audio and sync only within its coverage.
- **Technical probe:** actual encoded-file properties. Does not establish aesthetic or perceptual success.
- **Rights review:** exact subject/use and per-asset permissions. Distinct from technical success.

P35 preserves static/still versus moving-review distinctions from source reports. P33’s 2.5s/50% note window and P34’s 9px blur belong only to the historical eCPM films. Apply the general authored factual-accuracy requirement without promoting those measurements to universal thresholds.

## Handoff — authored C06/C07

```text
Achieved artifact: <actual path/state>
Required output versus observed output: <spec and probe result>
Review: <nine dimension statuses; observation coverage>
Rights: <subject/use and asset status>
Reproducibility: <exact environment and actual repeat coverage>
Remaining gaps/failed requirements: <specific items>
Next concrete dependency/review: <what remains before the requested final state>
```

Authored rubric/state provenance: [C06/C07](provenance.json). Historical author reports and the operation nulls below remain separate from this package policy.


## Admitted operations and boundaries

<a id="p33"></a>

### P33 — Give the eCPM source note its documented visibility window

**Admission:** Scoped. **Exact scope:** Author historical 2026-09-07 eCPM film note-visibility revision: 40–70 characters, earlier block, >=2.5s at >=50% opacity. No universal reading floor or acquired output/comprehension evidence.

**Condition:** The 40–70 character source note arrives in the final caption block with only 0.97–1.7 seconds at half opacity. (Evidence: R07-F005.)

**Action:** For this film, move the source/explanatory note to the first or second caption block to permit at least 2.5 seconds at at least 50% opacity. (Evidence: R07-F005.)

**Recovery:** Move the late note earlier in the same shot rather than leave the factual correction too late to read. (Evidence: R07-F005.)

**Verification:** Evaluate the note’s actual visible timing in this local treatment; the stated eight revisions and thresholds are author reports. (Evidence: R07-F005.)

**Boundaries:** No source/output chain or comprehension study acquired. Do not reuse 2.5 seconds or 50% as a global reading floor.

**Admission confidence:** {"admission_basis": "source_local_case_or_profile", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "not_applicable_or_case_limited", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R07-F005:** origin `author_stated_historical_revision`; confidence `high for documented contract; medium for author historical accounts; perception unverified`; observed: Historical account read; no recreated or observed frames Relation: `changed`. Boundary: Reported2026-09-07 eCPM production; author thresholds are scoped to this film. No source/output chain or reader-comprehension study acquired.

**Sources:** [R02-S007](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/reference/lessons.md) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P33` when tracing a decision.

<a id="p34"></a>

### P34 — Prevent factual eCPM animation from displaying unsourced intermediate numerals

**Admission:** Scoped. **Exact scope:** Author historical eCPM factual-year/duration/money-counter repair: unsourced readable intermediates versus blurred/removed counter. 9px is film-local; labeled illustrative values are separate conditions.

**Condition:** A factual counter visibly passes through unsourced years, durations or monetary values before its verified endpoint. (Evidence: R07-F007.)

**Action:** For this film, make intermediate values unreadable or remove the counter; the reported YearRoll treatment keeps blur at least 9px until landing and then removes it. Check formula/example label consistency. (Evidence: R07-F007.)

**Recovery:** Remove or obscure the unsupported factual intermediates while retaining the verified landing value. (Evidence: R07-F007.)

**Verification:** Include a literal-value scan and frame inspection: this author reports a counter escaping four pixel-QC reviewers. (Evidence: R07-F007.)

**Boundaries:** Historical account only, no frames acquired. 9px is local; clearly labeled illustrative examples are a different condition, and this is not a ban on all numerical interpolation.

**Admission confidence:** {"admission_basis": "source_local_case_or_profile", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "not_applicable_or_case_limited", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R07-F007:** origin `author_stated_historical_revision`; confidence `high for documented contract; medium for author historical accounts; perception unverified`; observed: No source exact artifact or frames acquired Relation: `changed`. Boundary: eCPM historical account only; avoid universal blur9px. Intermediate values of an explicitly labelled illustrative example differ from factual years/measurements; no broad animation prohibition supported.

**Sources:** [R02-S007](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/reference/lessons.md) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P34` when tracing a decision.

<a id="p35"></a>

### P35 — Separate static, sampled-frame and continuous-motion quality evidence

**Admission:** Scoped. **Exact scope:** Project Bright static/still versus human-motion verdict and RAG author consecutive-transition/caption QC only. Neither cut was independently watched/listened; no universal score/quality pass threshold.

**Condition:** The cut passes static checks or still-image review but pacing, motion and dynamic caption behavior must be assessed. (Evidence: R08-F003, R08-F005.)

**Action:** Use static checks for their declared coverage, then inspect consecutive transition/caption frames and reserve continuous pacing/countdown/drama judgments for actual viewing. (Evidence: R08-F003, R08-F005.)

**Recovery:** `null` — unsupported; do not fill this operation component. (Evidence: none.)

**Verification:** Report static/still results separately from actual full-motion review; a dynamic-caption detector can miss content, and stills cannot establish continuous beat pacing. (Evidence: R08-F003.)

**Boundaries:** Research read source reports and did not watch the Bright/RAG cuts or listen. Source-reported human verdict is not an independent observed success.

**Admission confidence:** {"admission_basis": "source_local_case_or_profile", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "not_applicable_or_case_limited", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R08-F003:** origin `author_stated`; confidence `high documented boundary; medium author-reported outcomes`; observed: First-party text/source read; no controlled production trial Relation: `changed`. Boundary: Source states stills cannot judge dynamics; later human feedback is author report. R08 did not watch this cut or listen; no numerical universal score threshold

**R08-F005:** origin `author_stated`; confidence `high documented boundary; medium author-reported outcomes`; observed: Read actual v1/v3QC source; source-reported differences, no media playback Relation: `changed`. Boundary: Author reports include full frame sequence/pixel measurements and contact strips, not researcher full playback/audio evidence; exact frame/pixel tolerances are film-local

**Sources:** [R02-S005](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/examples/rag/qc/qc_v1_C2.md) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`); [R02-S006](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/examples/rag/qc/qc_v3_final.md) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`); [R02-S025](https://github.com/tradewithmeai/project-bright/blob/41b3a17c1e49663e86810c3e3eada7cba2316c2d/apps/claude-remotion/.claude/skills/judge-video/LOOP_LOG.md) (revision `41b3a17c1e49663e86810c3e3eada7cba2316c2d`); [R02-S026](https://github.com/tradewithmeai/project-bright/blob/41b3a17c1e49663e86810c3e3eada7cba2316c2d/apps/claude-remotion/remotion_lab/experiments/ai_top5_001/VERDICT.md) (revision `41b3a17c1e49663e86810c3e3eada7cba2316c2d`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P35` when tracing a decision.
