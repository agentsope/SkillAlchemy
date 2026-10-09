---
name: agentsope-ai-video-director
description: >-
  Direct and implement programmatic videos from a natural-language sentence: brief,
  shots, style, timeline, assets, engine-specific coding prompts, draft, review and
  repair. Use when asked to make a video, product launch, explainer, Reel/Short,
  kinetic typography or docs-to-video with HyperFrames, Remotion or Motion Canvas,
  or to improve an existing code-video project. 一句话视频制作与导演工作流。
---
# AI Video Director

## Activation Rules

Use this skill for an authorized video-production task, including:
- “用一句话做一个 15 秒产品发布视频。”
- “Turn this data into a 30-second animated explainer.”
- “Make a narrated video from these authorized docs.”
- “Write the coding-agent prompt and render this Remotion/HyperFrames video.”
- “The captions overlap in this code-video project; inspect and repair it.”

Do not activate solely for:
- A general question about cinema history or a filmmaker.
- A request to summarize a document with no video deliverable.
- A still-image request with no video intent.
- An unrelated React/Vite bug without a video composition.
- A diffusion-model prompt request alone: that extension has not been distilled.

## Agentic Protocol

Execute the following authored application chain (C01–C09).
Every step produces a retained result before its dependent step starts.
Read [operation cards](references/sop_models.md) and match each operation’s exact scope before use.
Do not turn a source-local case into a rule for a new film.

### 1. Turn the sentence into a brief

Read [prompt fields](references/prompt-patterns.md).
Extract goal, audience, main message, platform, supplied facts, duration/aspect,
language, audio intent, assets, engine preference and delivery requirements.
Preserve explicit values. Mark inferred audience, style and format as assumptions.
If unstated, use these reversible **package defaults**, subject to user context:
15s for a short product/social draft; 30s for a compact data explanation;
60s for a compact docs/knowledge draft; 30fps; 16:9 for general explainers,
9:16 when vertical social is explicit; original geometric visuals and system fonts.
These values are authored conventions, not evidence-proven creative optima.
Retain supplied facts with their source. Record unknown facts and synthetic placeholders separately.
A missing product metric must not become a fabricated benefit claim.
Clarify only critical facts, permissions or assets that prevent the requested result;
continue a provisional brief and authorized work while those inputs are pending.
Output `director_brief` with `declared`, `assumptions`, `facts`, `unknowns` and `audio_intent`.

### 2. Make the engine-neutral director plan

Read the matching [video guide](references/video-types.md) and
[director fields](references/director-playbook.md).
Choose an authored communicative pattern from the goal and available material.
Write a shot table: ID, interval in seconds, subject/focal action, framing/layout,
exact copy, animation intent, transition, asset, audio/caption cue and acceptance.
Close the timeline at the declared duration; record intentional overlaps or gaps.
Define palette, typography, hierarchy, backgrounds, safe-area assumptions and motion intent.
Build an asset ledger with provenance, permission, intended use and unresolved rights.
Keep original synthetic visuals available when third-party assets are pending.
For voice-led work, use real authorized audio timing when ready (P28);
if audio is pending, label the entire scene/caption clock provisional.
Do not apply P05’s 2–10-minute or P06’s 90–180-second guidance to short examples as proven rules.
P02/P05/P06/P09 are optional author suggestions, 待验证; they are never quality guarantees.
Output `director_plan`: brief, shots, style tokens, timeline, assets, audio, target and acceptance.

### 3. Probe and route the environment

Read [isolated adapters](references/engine-adapters.md).
Probe actual Node, browser, FFmpeg/exporter, installed versions and local scripts;
record command output/version/license evidence and missing capabilities.
Use an existing compatible project when available; do not silently upgrade it.
Select HyperFrames only within the verified 0.8.142 profile and its local dependencies.
Select Remotion server only with matched 4.0.534 packages, browser and intended-use eligibility (P37).
Its browser compositor is a separate route with its own supported DOM/media/codec subset (P23).
Motion Canvas 3.17.2 uses its Vite editor and registered FFmpeg exporter (P25),
not a fabricated headless render CLI. Preserve release/main and binary-license distinctions (P39).
The Canvas/WebGL renderer is only the recorded source-local profile (P27),
not a universal fallback to recreate or vendor.
Do not buy services or assets. If production rights are unknown, retain the plan/prompt,
use only eligible authorized work and report the unresolved eligibility.
If no runnable eligible exporter exists, output its concrete gap and the achieved state.
Output `engine_route`: engine/profile/version, environment evidence, eligibility and gaps.

### 4. Compile one engine-specific coding prompt

Read the selected adapter’s exact contract and relevant
[HyperFrames example](examples/hyperframes-prompt.md) or
[Remotion example](examples/remotion-prompt.md).
Include the complete director brief, shot table, style, timeline, asset ledger,
audio/caption timing, dependency pins, file/output requirements and acceptance.
Include only the selected adapter’s admitted API/CLI bindings.
For HyperFrames, seconds, static finite root duration and completed paused registration apply (P16–P19).
For Remotion, frame-derived state, zero-based local Sequence clocks and explicit clamps apply (P21).
Audio fields use frames; Caption fields use milliseconds (P40).
For Motion Canvas, generator `yield*` timing uses seconds and persisted event metadata (P25/P31).
Never transpose APIs or clock units between engines.
Specify an actual draft, relevant static/render checks, repair and state report as outputs.
Output `engine_prompt` with the engine identity at its start; never join adapter templates.

### 5. Implement and produce the actual draft

When the chosen environment permits, create original project files and assets,
execute its admitted preview/render path and retain logs, exit codes and output paths.
Do not stop at a prompt when implementation/rendering is authorized and feasible.
If a dependency, critical fact or right blocks a step, preserve the implemented work,
state the exact blocker, and deliver the reachable plan/prompt/code result.
Check the resulting artifact exists; a successful-looking log is not the video.
Output code and an encoded draft only when those artifacts were actually created.
Keep `plan_available`, `code_available` and `encoded_artifact_available` independent.

### 6. Inspect the achieved result

Read [quality rubric](references/quality-rubric.md) and
[checklist](tests/quality-checklist.md).
Check narrative, visual consistency, pacing, animation, legibility, facts, audio,
technical correctness and reproducibility against the declared acceptance.
Run static syntax/resource/timeline checks that the project actually supports.
For encoded drafts, inspect technical metadata, representative and consecutive frames,
then watch full motion and listen when the tools permit; record each coverage separately.
A sampled frame cannot establish continuous pacing or audible synchronization (P35).
For narrated intent without audio, mark audio failed/pending; do not mark listening unnecessary.
Record pass/fail/warning/unknown/not_executed/not_applicable with evidence per dimension.
Output `qa_report`; call a result reviewed only for checks actually performed.

### 7. Repair and hand off truthfully

Turn observed defects into specific shot/code/asset/timing changes.
Use candidate recovery only when its card contains an admitted recovery within scope;
otherwise apply the explicit authored acceptance requirement and label its origin C06.
Rerun affected static/render/frame/motion/audio checks after the change.
Preserve the initial defect, change and new evidence; do not silently replace a failed verdict.
Deliver the current video/code/plan paths, resolved assumptions, sources/rights,
engine/version, commands used, review coverage and remaining gaps.
Record all independent artifact states in the handoff, including preview, encode,
technical probe, sampled frames, full-motion review, listening and reproducibility.
An unexecuted check stays unexecuted even when a different check passed.
Use [manual review](tests/manual-review.md) and its output record contract for evaluation.

## Core Operation Models

General means reusable **inside its exact scope**, not universal or visually validated.
Full cards preserve 40 admissions and every absent recovery/verification component.

| Model | Use within its card’s scope | Primary action |
|---|---|---|
| H1 / P02 | Optional HyperFrames prompt control | Choose delegated aesthetics or explicit layout/timing |
| H2 / P05–P06 | Optional long/structured explainers | Word-led question or scene-frame budget |
| H3 / P09 | Optional Lemo dense sonification/occlusion | Style-local note/pen adjustments |
| H4 / P15 | TikTok auction ad placement only | Match its actual overlay template |
| M1 / P16–P19 | HyperFrames 0.8.142 GSAP profile | Seconds, root/IDs, readiness, ownership |
| M2 / P21–P24 | Remotion 4.0.534 isolated routes | Frame state, export, resource handles |
| M3 / P25–P26/P31 | Released Motion Canvas 3.17.2 | Editor exporter, audio, event metadata |
| M4 / P28/P40 | Ready/pending voice; typed units | Provisional audio or measured clock translation |
| M5 / P37–P38 | Intended use and source-derived assets | Resolve engine and individual asset permissions |

Scoped P01/P03–P04/P07–P08/P10–P14/P20/P27/P29–P30/P32–P36/P39
are conditional source notes in the cards and [case ledger](references/case-studies.md).
Read their source/version/condition before consulting a note; no scoped aesthetic is a generic prescription.
Authored C01–C09 define this package’s workflow/schema/evaluation; empirical evidence IDs are empty for them.
Rule→finding→source/version trace and exact bindings are in [provenance](references/provenance.json).

## Output Style

Lead with the concrete result and actual artifact state.
Use Chinese or the user’s language for useful directions; retain exact API names and units.
Use concise prose plus shot/timeline tables when they help review the film.
Mark assumptions, supplied facts and unknowns explicitly; never present a placeholder as fact.
A coding prompt includes implementable detail, not merely mood words.
Forbidden boilerplate: “Analyzing this with the framework…”, “Following the model card…”,
“Let me analyze this systematically…”, “Would you like me to expand further?”
Cite the original source naturally; keep operation IDs in trace metadata, not promotional claims.
Routine reversible implementation choices do not require an extra approval milestone.

## Output Modes

| Mode | Concrete deliverable | State rule |
|---|---|---|
| Director plan | Brief, shots, style, timeline, assets | Plan available; no render implied |
| Engine prompt | Isolated versioned coding-agent prompt | Prompt available; no code implied |
| Implementation | Original code/assets and execution log | State actual files and blocked steps |
| Rendered draft / QA | Encoded artifact and covered checks | Encoding and review remain independent |
| Repair | Defect, code/timing change, rerun evidence | Only affected checked states advance |
| Handoff | Paths, states, commands, rights, gaps | Unknown/unexecuted states remain visible |

## Boundary Rules

1. Scope: coding-agent programmatic video; diffusion remains a separate undistilled extension.
2. Sources: only admitted P01–P40 within exact scopes plus explicit authored C01–C09;
   research cases and structural exemplars never supply additional procedures.
3. Evidence: P02/P05/P06/P09 are optional unverified author guidance;
   source claims, code inspection, sampled observation and audiovisual validation differ.
4. Versions: technical knowledge snapshot 2026-10-09; verify exact pins/revision/license
   before applying another version. No blanket equivalence from a version string.
5. Rights: original package MIT; third-party code/media/fonts/music/services retain
   separate terms. Remotion production eligibility and unknown asset rights require resolution.
6. Engine isolation: seconds, zero-based frames, caption milliseconds and upstream
   inclusive one-based frame tables must be explicitly translated; no mixed CLI/API namespaces.
7. Capability: probe tools and create the best authorized concrete artifact available;
   missing tools/rights/facts are reported, and no purchased service is presumed.
8. Honesty: static success, preview, encode, sampled frames, full-motion viewing and
   listening establish separate states; cinematic/language/audio/diffusion coverage has limits.

## References

| Resource | Load when |
|---|---|
| [Prompt patterns](references/prompt-patterns.md) | Normalize input and write a coding brief |
| [Director playbook](references/director-playbook.md) | Fill shot/style/timeline/asset fields |
| [Video types](references/video-types.md) | Choose one of seven authored guides |
| [Engine adapters](references/engine-adapters.md) | Probe, route and implement one engine |
| [Quality rubric](references/quality-rubric.md) | Inspect/revise actual artifacts |
| [Operation cards](references/sop_models.md) | Match exact admitted scopes before acting |
| [Source index](references/sources.md) | Verify author/version/rights |
| [Case studies](references/case-studies.md) | Consult provenance and source-local examples |
| [Research notes](references/research_notes.md) | Understand coverage and verification limits |
| [Provenance](references/provenance.json) | Trace rules, nulls, bindings and aliases |
| [Package guide](README.md) | Install locally, browse examples/tests and run checks |
