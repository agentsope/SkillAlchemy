# Director playbook

Use this guide after [prompt-patterns.md](prompt-patterns.md). Produce a director plan whose intent, shots, style, assets, audio and acceptance can be translated by one [engine adapter](engine-adapters.md). The planning schema and checks below are authored C01/C03/C06. Admitted creative techniques remain scoped notes; none establishes one required look or narrative for every video.

## Produce the plan — authored C01/C03

1. State the audience, main message and intended viewer action in the brief’s terms. Keep factual provenance next to the claims that appear on screen or in narration.
2. Choose the applicable [video-type guide](video-types.md) from communicative intent, assets and timing constraints. Write a narrative and shot table rather than selecting an arc from genre alone.
3. Fill each shot’s subject, focal action, framing, layout, literal copy, timing and transition. Mark unresolved choices as assumptions or unknowns. Refer to a P ID only when its exact condition and scope match.
4. Define project-specific style tokens and an asset/rights ledger. Record how color, typography, depth, camera and motion serve the stated intent; these are authored project choices, not universal style prescriptions.
5. Build audio/caption cues from the actual audio state. If voiced audio is pending, mark alignment and duration provisional. Translate units only after selecting an adapter.
6. Close the timeline against the target duration, carrying each shot’s seconds and any deliberate overlap explicitly. Write acceptance criteria and hand off the plan to the selected adapter.

## Shot and timeline schema — authored C03

| Field | Required meaning | Validation |
|---|---|---|
| `shot_id` | Unique reference for implementation and revision | No ambiguous duplicate IDs |
| `start_seconds`, `end_seconds` | Engine-neutral intended interval | End follows start; timeline matches declared target or reports a gap |
| `subject`, `focal_action` | What is present and what changes | Explicit enough to implement |
| `framing`, `layout` | Camera/view and placement decisions | Assumptions recorded; required relationships explicit |
| `copy` | Literal on-screen text and/or narration | Source, supplied, unknown or synthetic status retained |
| `transition` | Outgoing/incoming relationship | State whether overlap is intended; do not infer a universal nonoverlap rule |
| `assets` | Local assets required by the shot | Asset ledger and rights status linked |
| `audio_cues`, `caption_cues` | Timing data and units | Ready or provisional status explicit |
| `acceptance` | Observable required result | Observation method and actual coverage recorded |

The plan can hold cue IDs in addition to seconds, but the engine owns their implementation semantics. Keep Motion Canvas named editor events separate from RAG frame constants and Remotion frame functions.

## Style and asset ledger — authored C03

```yaml
style_tokens:
  colors: {background: null, foreground: null, emphasis: null}
  typography: {family: null, source_and_rights: null, hierarchy: null}
  layout: {aspect: null, subject_regions: null, copy_regions: null}
  motion: {camera_intent: null, easing_intent: null, continuity: null}
assets_and_rights:
  - asset_id: "project identifier"
    kind: "image | footage | font | music | voice | other"
    source: null
    permission: "confirmed | unknown | disallowed"
    intended_use: "exact project/platform/use"
    local_location: null
    attribution_or_notice: null
```

Do not fill missing permission from the repository’s license. Engine eligibility is a separate C05 decision. A synthetic visual substitute must be recorded as such and must still fulfill the user’s authorized intent.

## Audio and captions

For the Anything2Explainer voiced pipeline, P28 distinguishes ready measured audio from pending audio and empty templates. P29 preserves WordBoundary semantics and labels interpolation approximate; P30 requires retiming after changed words/voice/rate/pauses in its hard-coded RAG storyboard. These source workflows do not establish perceptual sync or a silent-versus-voiced creative rule.

For Motion Canvas cues use P31 in [engine-adapters.md](engine-adapters.md#p31). For Remotion audio frames/Caption milliseconds and upstream one-based inclusive frame-table translation use P40 in [engine-adapters.md](engine-adapters.md#p40). Never transpose those APIs into another engine.

## Conditional layout and repair notes

P04 covers an explicitly prohibited counter/title overlap in the recorded HyperFrames rewrite; intentional overlap remains a valid project choice. P13 preserves landscape versus portrait branches only for its legacy/Cinematic embedded-caption module. P14’s crown repair depends on the documented subject bias and phrase length. P15 applies only to the specified TikTok auction advertising placement; it supplies no universal safe-area percentage and no organic TikTok/Reels/Shorts/Douyin template.

P09’s density/decay ratio is optional style-local guidance pending validation. P10 addresses a reported overloaded drawing scheduler. P11’s transitions come from the particular kinetic-reel focal geometry. P32’s 300→80 px repair and caption coordinates remain RAG-film-local.

## Review and revise — authored C06/C07

Record the required relationship before inspecting it. Report whether static checks, sampled frames, consecutive boundary frames, full-motion viewing or listening actually covered it. Repair observed defects using the matching admitted recovery or explicit authored project requirements; keep the result and evidence state independent. Use [quality-rubric.md](quality-rubric.md) for the nine dimensions and [manual review](../tests/manual-review.md) for remaining human observations.

Authored planning/review provenance: [C01/C03/C06/C07](provenance.json). Null recovery/verification fields below are not filled by this authored planning policy.


## Admitted operations and boundaries

<a id="p04"></a>

### P04 — Express a required nonoverlap boundary

**Admission:** Scoped. **Exact scope:** Recorded HyperFrames counter-to-READY rewrite and loader wording at 2dd708e0; required nonoverlap in those examples only; original failed artifact unavailable.

**Condition:** An outgoing counter must be gone before the next title appears. (Evidence: R01-F007.)

**Action:** State the outgoing fade completion before the incoming reveal begins; avoid assigning both events the same ambiguous instant when overlap is prohibited. (Evidence: R01-F007.)

**Recovery:** Rewrite the completion/start relationship after the documented counter/reveal collision. (Evidence: R01-F007.)

**Verification:** `null` — unsupported; do not fill this operation component. (Evidence: none.)

**Boundaries:** Author-reported rewrite; old artifact absent and current one-second samples cannot prove the exact boundary. Intentional overlap remains allowed.

**Admission confidence:** {"admission_basis": "source_local_case_or_profile", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "not_applicable_or_case_limited", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R01-F007:** origin `author_stated`; confidence `medium`; observed: Loader samples inspected, insufficient temporal resolution to confirm absence of all overlap Relation: `changed`. Boundary: Author-reported rewrite; old artifact absent; this is sequencing specificity, not stylistic universal

**Sources:** [R01-S001](https://github.com/heygen-com/hyperframes/blob/2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2/docs/prompting/examples.mdx) (revision `2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2`); [R01-S002](https://github.com/heygen-com/hyperframes/blob/2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2/docs/prompting/anatomy.mdx) (revision `2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2`); [R01-S021](https://static.heygen.ai/hyperframes-oss/docs/images/prompting/example-loader-ready.mp4) (revision `unresolved`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P04` when tracing a decision.

<a id="p09"></a>

### P09 — Handle dense sonification and pen occlusion within the dataviz style

**Admission:** General. **Exact scope:** Optional Lemo Data Storytelling style contract at 4d7014aa7ba7d22c00513052dd996a4f200d5102, specifically dense note passages or pen-body occlusion. The 1.5 ratio is style-local and empirically unverified.

**Condition:** Within this style, note gaps become dense or the drawing pen body covers fresh marks. (Evidence: R02-F002.)

**Action:** Optional source-authored guidance (empirical effectiveness not verified): Make dense-passage notes quieter, keep their decay no longer than 1.5 times the note gap, and steepen the pen angle when its body obscures newly drawn marks. (Evidence: R02-F002.)

**Recovery:** Use the source’s density-dependent audio and pen treatment for that obstruction symptom. (Evidence: R02-F002.)

**Verification:** `null` — unsupported; do not fill this operation component. (Evidence: none.)

**Boundaries:** Explicit source applicability boundary; no local audio/render measurement. The 1.5 ratio is confined to this style and is not a universal mix rule.

**Admission confidence:** {"admission_basis": "optional_author_guidance", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "not_applicable_or_case_limited", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R02-F002:** origin `documented_contract`; confidence `medium`; observed: Changed relation relies on explicit dense-passage boundary, not a controlled rendered A/B. Actual early/late demo phases also change values and narrative position; that observational comparison is confounded. No audio level or rendering measurement. Relation: `changed`. Boundary: Conditional recommendations in Data Storytelling style for dense passages; cadence changes within one film, not proof for all video genres.

**Sources:** [R02-S018](https://github.com/lemomo-ai/lemo-opuscar/blob/4d7014aa7ba7d22c00513052dd996a4f200d5102/styles/dataviz/DEMO.md) (revision `4d7014aa7ba7d22c00513052dd996a4f200d5102`); [R02-S019](https://github.com/lemomo-ai/lemo-opuscar/blob/4d7014aa7ba7d22c00513052dd996a4f200d5102/styles/dataviz/STYLE.md) (revision `4d7014aa7ba7d22c00513052dd996a4f200d5102`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P09` when tracing a decision.

<a id="p10"></a>

### P10 — Recover when one drawing performer misses spoken deadlines

**Admission:** Scoped. **Exact scope:** Einstein in Your Pocket whiteboard production case at Lemo 4d7014aa: source-reported overloaded one-pen scheduler, explicit completion windows and extra pen capacity only.

**Condition:** Overlapping drawing work in the one-pen scheduler accumulates delay; satellites were author-reported twelve seconds late. (Evidence: R02-F006.)

**Action:** Give drawing jobs explicit completion windows and allocate another pen to overlapping jobs while retaining the word-timing anchors. (Evidence: R02-F006.)

**Recovery:** Replace the overloaded single queue with bounded windows and additional drawing capacity for this film. (Evidence: R02-F006.)

**Verification:** `null` — unsupported; do not fill this operation component. (Evidence: none.)

**Boundaries:** Real source-described recovery, no old/new render or measured benchmark. Workload and treatment changed together; no load-only causal claim.

**Admission confidence:** {"admission_basis": "source_local_case_or_profile", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "not_applicable_or_case_limited", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R02-F006:** origin `author_stated`; confidence `medium`; observed: Specific failure/recovery described; no inspected old render or benchmark. Relation: `unresolved`. Boundary: Real production recovery, but workload and scheduler treatment changed together; no matched load-only pair.

**Sources:** [R02-S021](https://github.com/lemomo-ai/lemo-opuscar/blob/4d7014aa7ba7d22c00513052dd996a4f200d5102/styles/whiteboard/DEMO.md) (revision `4d7014aa7ba7d22c00513052dd996a4f200d5102`); [R02-S022](https://github.com/lemomo-ai/lemo-opuscar/blob/4d7014aa7ba7d22c00513052dd996a4f200d5102/styles/whiteboard/demo/film.js) (revision `4d7014aa7ba7d22c00513052dd996a4f200d5102`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P10` when tracing a decision.

<a id="p11"></a>

### P11 — Choose transitions from outgoing visual focus in the kinetic-reel demo

**Admission:** Scoped. **Exact scope:** Visualx kinetic-reel 17-second OPEN/TITLE/STAT/FLOW/QUOTE/END code demo at 18c8426fe97c1353dc62afd584f7ac8e39ad64bd only.

**Condition:** This demo changes between title, metric and state-machine chapters using its shared cue file. (Evidence: R03-F007.)

**Action:** Use the outgoing focal geometry to select the demo’s zoom, iris or wipe, and align scene/music hits through the shared cue file. (Evidence: R03-F007.)

**Recovery:** `null` — unsupported; do not fill this operation component. (Evidence: none.)

**Verification:** `null` — unsupported; do not fill this operation component. (Evidence: none.)

**Boundaries:** Code inspection only; no rendered audit or universal transition/easing prescription.

**Admission confidence:** {"admission_basis": "source_local_case_or_profile", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "not_applicable_or_case_limited", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R03-F007:** origin `researcher_inferred`; confidence `medium`; observed: Specific code read; neither demo rendered in this audit Relation: `unresolved`. Boundary: Different engine/story/style/duration; no matched atomic contrast. Purposeful transitions/camera are source-local observations, not universal transition/easing defaults

**Sources:** [R03-S005](https://github.com/VisualxIntelligence/motion-tools-and-skills/blob/18c8426fe97c1353dc62afd584f7ac8e39ad64bd/skills/kinetic-reel/template/reel/reel.js) (revision `18c8426fe97c1353dc62afd584f7ac8e39ad64bd`); [R03-S025](https://github.com/VisualxIntelligence/motion-tools-and-skills/blob/18c8426fe97c1353dc62afd584f7ac8e39ad64bd/skills/kinetic-reel/template/reel/cues.js) (revision `18c8426fe97c1353dc62afd584f7ac8e39ad64bd`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P11` when tracing a decision.

<a id="p13"></a>

### P13 — Adapt the recorded embedded-caption layout to aspect ratio

**Admission:** Scoped. **Exact scope:** Recorded legacy/Cinematic subject-aware embedded-captions layout profile at HyperFrames 2dd708e0, English interview/caption context with no platform UI. Side-plane/top-band heuristics do not cover Standard mode, every caption mode or every HyperFrames film.

**Condition:** This specific caption module’s layout is being applied in landscape or portrait. (Evidence: R03-F001.)

**Action:** Preserve the recorded conditional layouts: landscape uses a clean side caption plane and conditional crown; portrait replaces the side plane with a full-width top band and optional crown below. (Evidence: R03-F001.)

**Recovery:** `null` — unsupported; do not fill this operation component. (Evidence: none.)

**Verification:** `null` — unsupported; do not fill this operation component. (Evidence: none.)

**Conditional branches (retain separately):**

- 16:9 recorded module profile → Side caption plane; crown only where applicable.

- 9:16 recorded module profile → Full-width top band; optional crown below.

**Boundaries:** Approximate 20% band and 4% broadcast margin are module heuristics. Current Standard/Cinematic modes differ; this legacy reference conditional is not asserted for every current caption mode or platform. No rendered aspect A/B.

**Admission confidence:** {"admission_basis": "source_local_case_or_profile", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "not_applicable_or_case_limited", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R03-F001:** origin `documented_contract`; confidence `high`; observed: Read source aspect conditional; no re-rendered16:9/9:16 controlled pair; condition/action boundary documented only Relation: `changed`. Boundary: This is embedded-captions module, subject/foreground-aware layout; approximate20% band and4% broadcast margin are module heuristics, not universal video/platform requirements Current snapshot also contains Standard/Cinematic modes. The legacy reference conditional is not a contract for every current caption mode.

**Sources:** [R03-S017](https://github.com/heygen-com/hyperframes/blob/2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2/skills/embedded-captions/references/layout-heuristics.md) (revision `2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2`); [R03-S019](https://github.com/heygen-com/hyperframes/blob/2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2/skills/embedded-captions/references/example-renders/champion.html) (revision `2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P13` when tracing a decision.

<a id="p14"></a>

### P14 — Place or demote the crown in the documented interview layout

**Admission:** Scoped. **Exact scope:** Source-reported Jobs/Champion landscape interview crown-placement dilemma at HyperFrames 2dd708e0, with the recorded subject bias and phrase-length conditions only.

**Condition:** The Jobs subject is right-biased and the short centered crown is largely swallowed, unlike the centered Champion layout. (Evidence: R03-F005.)

**Action:** For the documented Jobs geometry, move the crown into the larger clean left zone or demote it to emphasis rather than retain the centered title. (Evidence: R03-F005.)

**Recovery:** Apply the documented relocation/demotion to this occlusion symptom. (Evidence: R03-F005.)

**Verification:** `null` — unsupported; do not fill this operation component. (Evidence: none.)

**Boundaries:** Subject position and phrase length both changed; source-local repair, not an atomic aspect/language rule. No interview render was viewed.

**Admission confidence:** {"admission_basis": "source_local_case_or_profile", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "not_applicable_or_case_limited", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R03-F005:** origin `author_stated`; confidence `medium`; observed: Read author documented failure/repair, current champion absolute-stacked code; no source interview render viewed Relation: `unresolved`. Boundary: Subject placement and phrase length both change; not atomic aspect evidence. Source-local layout dilemma supports geometry-aware hypothesis only

**Sources:** [R03-S017](https://github.com/heygen-com/hyperframes/blob/2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2/skills/embedded-captions/references/layout-heuristics.md) (revision `2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2`); [R03-S018](https://github.com/heygen-com/hyperframes/blob/2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2/skills/embedded-captions/references/failure-modes.md) (revision `2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2`); [R03-S019](https://github.com/heygen-com/hyperframes/blob/2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2/skills/embedded-captions/references/example-renders/champion.html) (revision `2dd708e0a214fa4b8bffadc6a13c7ff55ef954a2`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P14` when tracing a decision.

<a id="p15"></a>

### P15 — Apply the placement-specific overlay contract for TikTok auction ads

**Admission:** General. **Exact scope:** TikTok auction in-feed advertising placement and its caption/anchor overlay configuration, official page updated June 2026 and retrieved 2026-10-09. No organic TikTok/Reels/Shorts/Douyin or universal pixel-safe-area rule.

**Condition:** The video is delivered as the documented TikTok auction in-feed placement with its caption/anchor configuration. (Evidence: R03-F003.)

**Action:** Obtain and use the safe-zone template matching that placement and anchor/overlay configuration. (Evidence: R03-F003.)

**Recovery:** `null` — unsupported; do not fill this operation component. (Evidence: none.)

**Verification:** Review the platform preview while retaining the source’s device-preview limitations. (Evidence: R03-F003.)

**Boundaries:** Pixel template was not acquired in research. No safe-zone percentages inferred for organic TikTok, Reels, Shorts or Douyin; language is held fixed.

**Admission confidence:** {"admission_basis": "documented_technical_or_rights_contract", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "documented", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R03-F003:** origin `documented_contract`; confidence `high`; observed: Official June2026 page read; no actual asset/platform preview compared Relation: `changed`. Boundary: TikTok auction ads only; actual pixel safe-zone template not acquired. Organic TikTok,Reels,Shorts and Douyin unknown. Language held fixed here; do not combine withCJK account-name field limits

**Sources:** [R03-S022](https://ads.tiktok.com/resources/help/article/tiktok-auction-in-feed-ads?lang=en-GB) (revision `Official page last updated June2026; retrieved2026-10-09 Asia/Shanghai`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P15` when tracing a decision.

<a id="p28"></a>

### P28 — Resolve voice-led timing from ready audio instead of template placeholders

**Admission:** General. **Exact scope:** Anything2Explainer documented voiced production/supplied-audio pipeline at 735c79c8, with real waveform/per-line tables versus its explicitly empty templates. RAG/lecture observations do not establish silent-versus-voiced creative invariance or perceptual sync.

**Condition:** The voiced brief has measured authorized narration, or narration/audio supply is still pending. (Evidence: R07-F002, R07-F001.)

**Action:** With ready audio, read actual waveform/per-line timing and derive scene/subtitle tables from that clock. With pending audio, obtain authorized synthesis/supply first and mark storyboard duration/alignment provisional; empty subtitles and placeholder 300-frame tables are not completed narration. (Evidence: R07-F002, R07-F001.)

**Recovery:** `null` — unsupported; do not fill this operation component. (Evidence: none.)

**Verification:** Distinguish measured ready timing tables from empty templates; a supplied finished audio track can use the same downstream alignment tables. (Evidence: R07-F002.)

**Conditional branches (retain separately):**

- Authorized audio and measured timing ready → Build actual per-line/scene/subtitle timing.

- Voiced intent but audio pending → Obtain audio first; retain provisional timing and incomplete narration state.

**Boundaries:** No TTS invoked or audio listened. No held-fixed silent variant was acquired, so this does not infer a general silent-vs-voiced creative treatment.

**Admission confidence:** {"admission_basis": "documented_technical_or_rights_contract", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "documented", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R07-F001:** origin `author_stated + missing matched evidence`; confidence `high for documented contract; medium for author historical accounts; perception unverified`; observed: Read code/timing; no audio listened or silent comprehension measured Relation: `unresolved`. Boundary: No true narration/silent matched pair. OpenMontage empty-audio product fixture differs in facts, purpose and duration; not admissible as controlled opposite side.

**R07-F002:** origin `documented_workflow_contract`; confidence `high for documented contract; medium for author historical accounts; perception unverified`; observed: Read empty template and synthesis code; no TTS/provider invoked; RAG historical output author-stated Relation: `changed`. Boundary: Source-stated dependency, not an executed same-script before/after experiment. Pending text or placeholder frames cannot substantiate final aligned subtitles/completed narration.

**Sources:** [R02-S001](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/README.md) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`); [R02-S009](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/reference/narration-storyboard.md) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`); [R02-S010](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/template/scripts/tts_build.py) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`); [R07-S004](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/examples/rag/交付说明.md) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`); [R07-S008](https://github.com/nateherkai/hyperframes-student-kit/blob/0d30152a82b9ceb93cfdd9bdbf46f0d5ab3cde86/video-projects/aisoc-lesson-5-1/STORYBOARD.md) (revision `0d30152a82b9ceb93cfdd9bdbf46f0d5ab3cde86`); [R07-S009](https://github.com/nateherkai/hyperframes-student-kit/blob/0d30152a82b9ceb93cfdd9bdbf46f0d5ab3cde86/video-projects/aisoc-lesson-5-1/index.html) (revision `0d30152a82b9ceb93cfdd9bdbf46f0d5ab3cde86`); [R07-S010](https://github.com/nateherkai/hyperframes-student-kit/blob/0d30152a82b9ceb93cfdd9bdbf46f0d5ab3cde86/video-projects/aisoc-lesson-5-1/assets/transcript.json) (revision `0d30152a82b9ceb93cfdd9bdbf46f0d5ab3cde86`); [R07-S017](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/template/src/common/Subtitle.tsx) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`); [R07-S018](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/template/src/common/timeline.ts) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`); [R07-S019](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/template/src/common/subs.ts) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P28` when tracing a decision.

<a id="p29"></a>

### P29 — Preserve the boundary type and fallback quality in the recorded TTS alignment pipeline

**Admission:** Scoped. **Exact scope:** Anything2Explainer block-start algorithm at 735c79c8 paired with edge-tts 7.2.0 WordBoundary/SentenceBoundary constructor semantics. Interpolation and half-second displacement remain source-reported approximate fallback, not locally measured alignment.

**Condition:** Word-level block timing is required by this pipeline, but default sentence metadata or unmatched chunks may be present. (Evidence: R07-F003.)

**Action:** Request WordBoundary explicitly, map token/character cursors to block starts and subtract trimmed lead silence. Retain the source’s character-length interpolation only as a fallback for unmatched chunks. (Evidence: R07-F003.)

**Recovery:** Flag fallback alignment as approximate instead of treating produced WAV data alone as exact sync. (Evidence: R07-F003.)

**Verification:** The recorded implementation uses word-boundary block starts where matched and interpolation otherwise; the author-reported possible half-second displacement is not a local measurement, and produced WAV data does not establish exact sync. (Evidence: R07-F003.)

**Boundaries:** No transcription/forced alignment executed. Service/speaker/media permissions remain separate.

**Admission confidence:** {"admission_basis": "source_local_case_or_profile", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "not_applicable_or_case_limited", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R07-F003:** origin `dependency_code + author_documented_contract`; confidence `high for documented contract; medium for author historical accounts; perception unverified`; observed: No transcription/forced alignment executed Relation: `changed`. Boundary: 7.2.0 dependency constructor default independently checked. Claimed half-second is author report, not measured locally. Fallback still exists for unmatched chunks; produced wav alone does not establish exact alignment.

**Sources:** [R02-S010](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/template/scripts/tts_build.py) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`); [R07-S015](https://github.com/rany2/edge-tts/blob/7.2.0/src/edge_tts/communicate.py) (revision `7.2.0`); [R07-S016](https://github.com/rany2/edge-tts/blob/7.2.0/LICENSE) (revision `7.2.0`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P29` when tracing a decision.

<a id="p30"></a>

### P30 — Retiming a changed voice in the hard-coded RAG storyboard

**Admission:** Scoped. **Exact scope:** Anything2Explainer RAG storyboard with hard-coded shot frames at 735c79c8; changed spoken words/voice/rate/pauses require the source-described retiming. No changed-voice output pair observed.

**Condition:** Spoken words, voice, rate or pause duration changes after the RAG storyboard’s frame numbers are fixed. (Evidence: R07-F004.)

**Action:** Regenerate timing and retime every affected hard-coded shot and caption cue against the changed voice. (Evidence: R07-F004.)

**Recovery:** Rebuild the fixed-frame storyboard timing after a voice change instead of retaining the old frame constants. (Evidence: R07-F004.)

**Verification:** `null` — unsupported; do not fill this operation component. (Evidence: none.)

**Boundaries:** Source-stated dependency, no revised-voice audio pair acquired. Not evidence that every engine uses hard-coded shot frames.

**Admission confidence:** {"admission_basis": "source_local_case_or_profile", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "not_applicable_or_case_limited", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R07-F004:** origin `source_stated_boundary`; confidence `high for documented contract; medium for author historical accounts; perception unverified`; observed: Read pinned docs; no revised voice recording or re-render Relation: `changed`. Boundary: Separate engine contracts. RAG retiming statement is source local; Motion Canvas waitUntil events belong to3.17.2 and are not Remotion APIs. No actual revised-voice audio pair acquired.

**Sources:** [R02-S009](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/reference/narration-storyboard.md) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`); [R06-S005](https://github.com/motion-canvas/motion-canvas/blob/e735a995aa738ca682feb4204a39ee7db7b5d279/packages/docs/docs/getting-started/time-events.mdx) (revision `e735a995aa738ca682feb4204a39ee7db7b5d279`); [R07-S004](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/examples/rag/交付说明.md) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P30` when tracing a decision.

<a id="p32"></a>

### P32 — Repair animated geometry crossing the actual caption band

**Admission:** Scoped. **Exact scope:** RAG SC18/SC16 1280×720@30fps local caption-path/entry repairs and v1/v3 author QC at 735c79c8; literal 300→80px and frame/pixel conditions remain film-local.

**Condition:** SC18 plane contour motion crosses the active narration caption region at the recorded frames. (Evidence: R07-F006.)

**Action:** For this shot, reduce the plane travel from 300 to 80 pixels so the visible path stays above the caption band; the documented neighboring SC16 card repair uses horizontal entry and corrected first-frame timing. (Evidence: R07-F006.)

**Recovery:** Change the offending path and entry timing using the actual local caption region rather than a generic canvas margin. (Evidence: R07-F006.)

**Verification:** Recheck the source-recorded transition/caption regions through consecutive cue-boundary frames; final v3 QC reports residual repairs and two low issues. (Evidence: R08-F005.)

**Boundaries:** Source-author QC/fix reports, repaired video not independently inspected. No universal y637–690, 80px path or frame tolerance.

**Admission confidence:** {"admission_basis": "source_local_case_or_profile", "empirical_quality": "待验证 / not_verified", "finding_confidence_preserved_in_evidence": true}.

**Research verification state:** {"research_full_motion_review": "not_executed", "research_audio_listening": "not_executed", "empirical_effectiveness": "not_verified", "technical_contract": "not_applicable_or_case_limited", "runtime_observation": "Only observations in the finding/profile records apply; no broader executed validation inferred."}.

**R07-F006:** origin `author_stated_historical_qc_and_fix`; confidence `high for documented contract; medium for author historical accounts; perception unverified`; observed: Pinned QC and fix records read; this agent did not inspect repaired video Relation: `changed`. Boundary: One local1280x720@30fps case, already countedR02-C001. Do not generalize y637–690 or delta80/120 to every layout.

**R08-F005:** origin `author_stated`; confidence `high documented boundary; medium author-reported outcomes`; observed: Read actual v1/v3QC source; source-reported differences, no media playback Relation: `changed`. Boundary: Author reports include full frame sequence/pixel measurements and contact strips, not researcher full playback/audio evidence; exact frame/pixel tolerances are film-local

**Sources:** [R02-S005](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/examples/rag/qc/qc_v1_C2.md) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`); [R02-S006](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/examples/rag/qc/qc_v3_final.md) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`); [R07-S006](https://github.com/Vincentwei1021/anything2explainer/blob/735c79c8724e897e8971cd59dde7e5aa11e4d6ce/examples/rag/shots_src/G4/BUILD_NOTES.md) (revision `735c79c8724e897e8971cd59dde7e5aa11e4d6ce`).

Full component support and provenance: [operation cards](sop_models.md), [provenance](provenance.json), [source index](sources.md). Identify `P32` when tracing a decision.
