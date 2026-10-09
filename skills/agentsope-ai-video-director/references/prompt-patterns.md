# Prompt patterns

Use this guide to normalize a sentence and create the framework-neutral brief. Read [director-playbook.md](director-playbook.md) to expand the brief, then select an isolated contract in [engine-adapters.md](engine-adapters.md). The schemas and sequence below are authored package policy C01–C03/C09; they are not a measured optimal prompt formula. Evidence-backed or source-local operations begin in the admitted-operation section.

## Normalize the request — authored C01/C02

1. Copy the user’s explicit goal, audience, message, platform, duration, aspect, audio intent, named assets and prohibitions without changing their meaning.
2. Separate supplied facts from externally sourced facts, unknown facts and synthetic placeholders. Give every factual claim a source or an explicit unknown/synthetic label. An invented product metric must stay visibly fictional in a demonstration.
3. Infer only reversible aesthetic choices needed to make the result concrete. Record each inferred choice as an assumption. Any chosen fps, duration, aspect, color, typeface or style is a package/project default, not a research-proven optimum.
4. Identify critical unknowns that prevent an authorized concrete result: missing factual material for a factual claim, unavailable required assets, unresolved intended-use rights, or a required renderer dependency. Ask only for the blocker; continue independent plan work.
5. Produce the brief below and a list of remaining gaps. A narration request with no audio remains narration-pending; do not silently turn it into a completed silent film.

## Brief schema — authored C03

The only required **input** is a natural-language video request. The fields below are required **outputs** of normalization and planning, not a form the user must fill. This field classification is authored C02/C03 application policy; it is not a newly admitted empirical prompt rule.

| Class | Fields | How to complete them |
|---|---|---|
| Necessary plan fields | Goal/intent, main message, supplied/sourced/unknown fact ledger, explicit constraints, shot table, closed timeline, style specification, asset ledger, audio state, target specification, acceptance and independent artifact states | Extract explicit values; otherwise derive the concrete plan or mark the unresolved factual/critical field unknown. An empty source/asset dependency must never become a claimed fact or available file. |
| Inferable when unstated | Audience, platform/placement, duration, aspect, fps, language, visual style, typography/layout/motion choices and provisional narrative | Use reversible package/project defaults only where context allows, label the assumption and preserve uncertainty. A platform assumption supplies no verified overlay contract. Critical content, permissions or required tools are not inferred as present. |
| Optional unless requested | Music/SFX, voice/provider, caption styling, branded logos/screenshots, specific camera/depth treatment, optional references, secondary delivery formats | Leave absent/null or propose a labeled choice. Once the user requests an item, track it as a requirement: missing assets/rights stay pending, and requested narration must not default to an intentionally silent finished deliverable. |

Explicit user choices override inferred defaults. Missing product names/claims, data units/periods, measured narration alignment, individual asset permissions and engine eligibility remain recorded unknowns or pending dependencies. Continue the authorized provisional plan and implementation steps that do not depend on them. A silent storyboard can be a labeled draft while narration is pending; it cannot satisfy the requested voiced film.

Required fields must be populated or explicitly marked unknown. Inferable fields must retain their assumption status. Optional fields may be null. A null authored field is different from a null admitted operation component: the latter stays unsupported even when C supplies a separate review policy.

```yaml
director_brief:
  intent: "required: intended outcome"
  audience: "required or explicitly unknown"
  main_message: "required: one stated message or unresolved alternatives"
  platform: "required or explicitly unknown"
  facts:
    - claim: "literal factual claim"
      origin: "supplied | sourced | unknown | synthetic"
      source: "source locator or null"
  constraints: ["user-stated requirements and prohibitions"]
  assumptions: ["reversible aesthetic/default choices with rationale"]
  narrative: "authored application of user intent; identify admitted operation if used"
  shots: []
  style_tokens: {}
  assets_and_rights: []
  audio_intent: "narrated | music/SFX | intentionally silent | unknown"
  captions_and_cues: []
  target_output: {duration_seconds: null, fps: null, width: null, height: null, format: null}
  engine_requirements: []
  engine_eligibility: "unknown until environment and rights are established"
  acceptance: []
  review_status: {}
```

Required output facts include actual artifact state, regardless of whether rendering succeeds. The full state model is in [quality-rubric.md](quality-rubric.md).

## Compile the coding-agent prompt — authored C01/C03/C05/C09

Use a self-contained prompt with these sections, filling from the approved brief rather than copying a full upstream prompt:

```text
Goal and audience: <brief values>
Main message and facts: <literal claims plus provenance/unknown/synthetic labels>
User constraints and assumptions: <separate lists>
Director plan: <shot IDs, subject, action, framing, layout, copy, seconds, transitions>
Style and assets: <project tokens plus asset-specific permissions>
Audio/captions: <intent, actual availability, cue units and provisional fields>
Engine: <one exact eligible versioned profile, dependency probe and rights basis>
Implementation contract: <only that adapter's admitted APIs/clock/readiness/export route>
Output and acceptance: <target specification, required observations and state report>
Remaining gaps: <critical unknowns; no claim of a video without an actual file>
```

Keep director intent separate from the adapter implementation. A shot duration in seconds is an engine-neutral planning field; the selected adapter translates it to that engine’s units. Use [HyperFrames prompt example](../examples/hyperframes-prompt.md) or [Remotion prompt example](../examples/remotion-prompt.md) only after selecting the corresponding eligible profile. New examples are synthetic applications.

## Prompt-control choices

P02 has two branches: delegate aesthetics with a mood-level brief, or state exact element/layout/timing values for a specific desired result. This is optional HyperFrames author guidance pending validation. It does not establish a universally effective palette or typography rule. P01 is limited to Coleam’s classic-short workflow, and P03 is the revised banknote-payoff case; do not turn either into a global default.

Authored policy provenance: [C01–C03/C05/C09](provenance.json). The concrete schema is package-authored; the operations below preserve their separate sources and confidence.


## Admitted operations and boundaries

<a id="p01"></a>

### P01 — Normalize a short topic before drafting sourced content

**Admission:** Scoped. **Exact scope:** Coleam classic-short topic-only factual-script workflow at 098505b5d6b14dfcf87a5a7a50241fd9a119eb6e; author-described workflow only.

**Condition:** A topic-only request is being developed through this creator workflow. (Evidence: R01-F003.)

**Action:** Normalize topic, slug, title and duration; obtain source-grounded research before writing factual script content. (Evidence: R01-F003.)

**Recovery:** `null` — unsupported; do not fill this operation component. (Evidence: none.)

**Verification:** `null` — unsupported; do not fill this operation component. (Evidence: none.)

**Boundaries:** No matched facts-present/facts-absent production pair. This is an author-stated workflow, not evidence that defaults improve every product video.

**Admission confidence:** {"admission_basis": "source_local_case_or_profile", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "not_applicable_or_case_limited", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R01-F003:** origin `author_stated`; confidence `low matched-pair support`; observed: Read source text/code; no controlled production experiment Relation: `unresolved`. Boundary: Source-local; no controlled independent replication

**Sources:** [R01-S006](https://github.com/coleam00/hyperframes-ai-video-generation/blob/098505b5d6b14dfcf87a5a7a50241fd9a119eb6e/.archon/workflows/create-classic-short.yaml) (revision `098505b5d6b14dfcf87a5a7a50241fd9a119eb6e`); [R01-S007](https://github.com/coleam00/hyperframes-ai-video-generation/blob/098505b5d6b14dfcf87a5a7a50241fd9a119eb6e/.archon/commands/create-classic-short.md) (revision `098505b5d6b14dfcf87a5a7a50241fd9a119eb6e`); [R01-S008](https://github.com/coleam00/hyperframes-ai-video-generation/blob/098505b5d6b14dfcf87a5a7a50241fd9a119eb6e/.claude/skills/diy-yt-creator/new-classic-short.md) (revision `098505b5d6b14dfcf87a5a7a50241fd9a119eb6e`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P01` when tracing a decision.

<a id="p02"></a>

### P02 — Choose how much aesthetic control to put into the coding-agent brief

**Admission:** General. **Exact scope:** Optional HyperFrames specification-dial prompt-control guidance at 2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2; delegating aesthetics versus specifying a particular appearance. No claim of validated visual effectiveness.

**Condition:** The brief either delegates aesthetic choices or requires a specific visual result. (Evidence: R01-F005.)

**Action:** Optional source-authored guidance (empirical effectiveness not verified): When delegating taste, state mood/style and allow choices. When exact control matters, state each relevant element’s shape, color, position and timing instead of leaving those choices implicit. (Evidence: R01-F005.)

**Recovery:** `null` — unsupported; do not fill this operation component. (Evidence: none.)

**Verification:** `null` — unsupported; do not fill this operation component. (Evidence: none.)

**Conditional branches (retain separately):**

- Aesthetic delegation is intended → Mood-level brief leaves colors and staging to the agent.

- A specific visual result is required → Supply explicit element/layout/timing values.

**Boundaries:** No same-task empirical comparison; no universal palette, gradient ban, typography size, camera motion or one-style rule.

**Admission confidence:** {"admission_basis": "optional_author_guidance", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "not_applicable_or_case_limited", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R01-F005:** origin `documented_contract`; confidence `low matched-pair support`; observed: Read source text/code; no controlled production experiment Relation: `unresolved`. Boundary: Guidance compares conceptual spec levels, not same-task empirical pair

**Sources:** [R01-S003](https://github.com/heygen-com/hyperframes/blob/2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2/docs/prompting/specification-dial.mdx) (revision `2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P02` when tracing a decision.

<a id="p03"></a>

### P03 — Keep a required payoff cue from disappearing during implementation

**Admission:** Scoped. **Exact scope:** HyperFrames stat-countup gallery R01-C001 revised banknote-payoff case; author-reported omission/rewrite and sampled revised frames only.

**Condition:** This countup needs the banknote payoff that an earlier author-described attempt omitted. (Evidence: R01-F004.)

**Action:** Name the banknote burst explicitly at the metric landing, state its settling window and retain the specified deterministic seed. (Evidence: R01-F004.)

**Recovery:** For this omitted-cue symptom, revise the brief to include the named payoff instead of relying on broad style language. (Evidence: R01-F004.)

**Verification:** Check the requested payoff in the output; the researched revised sample contains banknotes, while precise motion and the earlier output remain unobserved. (Evidence: R01-F004.)

**Boundaries:** Single author revision, earlier prompt/video absent. A spectacle is not required for other films.

**Admission confidence:** {"admission_basis": "source_local_case_or_profile", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "not_applicable_or_case_limited", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R01-F004:** origin `author_stated`; confidence `medium`; observed: Revised output sampled; pre-revision prompt/video absent Relation: `changed`. Boundary: Author-stated revision only; exact earlier prompt not published; not universal aesthetic default evidence

**Sources:** [R01-S001](https://github.com/heygen-com/hyperframes/blob/2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2/docs/prompting/examples.mdx) (revision `2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2`); [R01-S020](https://static.heygen.ai/hyperframes-oss/docs/images/prompting/example-stat-countup.mp4) (revision `unresolved`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P03` when tracing a decision.
