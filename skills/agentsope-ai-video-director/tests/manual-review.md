# Actual-output records and manual review

This is an authored C06–C08 evaluation convention. The JSON fixtures describe tests, with execution_status=not_executed. Actual actor execution records, logs and review evidence belong in a project-local audit directory outside the distributable runtime. Do not change the fixtures to claim their proposed checks passed. Read [sentence inputs](sentence-inputs.json), [routing cases](engine-routing.json), [negative cases](missing-and-errors.json) and [quality checklist](quality-checklist.md).

Run an actor against the compiled SKILL.md and relevant reference files. Retain the exact input, actor identity, time, loaded skill hash and actual emitted response. The actor must not copy these examples as a test result. Save its structured response as JSON, then index the real response in an envelope. P01, P02 and P03 actual records are required. Run negative/routing cases against actual available tools or explicitly controlled fixtures, and retain each fixture's limits. An environment fixture is not a claim about the user's computer.

```sh
python3 tests/validate_outputs.py --outputs <actual-output-envelope.json>
```

Only --outputs is accepted; there is no expected-response JSON argument. The stdlib validator reads retained actor response files and compares them with indexed outputs. It does not create responses, media or passing test data. A validator pass establishes the authored structural/behavior contract; full motion and listening still require actual observations. Known test IDs are checked against the exact authored input and their controlled routing/error contracts. These checks consume the fixture JSON as assertions, never as expected actor answers. Unknown benchmark IDs receive the generic contract checks; their specific intent still requires an independent review.

## Envelope schema

The top-level object has schema_version="1.0" and records, a list. Each record has:

| Field | Contract |
|---|---|
| test_id | Unique fixture ID; actual P01/P02/P03 required |
| input | Exact input given to the actor |
| actor | Actual actor identity |
| executed_at | Actual execution timestamp |
| loaded_skill_sha256 | 64 hex digits identifying the loaded SKILL.md |
| response_path | Actual retained response JSON, relative to the envelope directory or absolute |
| output | The same object parsed from response_path; equality is checked |

Output has plan, engine_route, coding_prompt, states, evidence, artifacts, qa and limitations. This schema is an authored output convention, not a new director procedure. Paths below are relative to the envelope directory. Do not enter paths for nonexistent files.

## Plan and route schema

plan contains nonempty intent/audience/main_message/platform/aspect_ratio/audio_intent strings; positive duration_seconds/fps/width/height numbers; facts/unknowns/assumptions/shots/assets lists; nonempty style object; timeline object; and audio object.

- facts: objects with key,value,origin and source. Origin is user,sourced,derived or synthetic. Sourced facts require a source. P02 retains user revenue values40/55 without invented dates/periods; derived+15/+37.5% must be labeled computations, not new observations.
- unknowns: names of unresolved factual/input fields. P01 retains product identity/features/claims; P02 units/periods/source/cause; P03 voice/audio rights/alignment and unread project facts.
- assumptions: objects with field,value,origin. Origin is package_default or user_assumption. Preserve user choices and label inferred reversible values.
- shots: objects with id,start_seconds,end_seconds,subject,action,framing,layout,copy,transition. Half-open intervals close from0 to target duration with tolerance1e-6. Intentional gaps/overlaps may be declared in timeline.intentional_gaps/intentional_overlaps as {start_seconds,end_seconds,reason}; each noncontiguous relationship must match an exact declared interval. Maximum shot end remains target duration. Remotion additionally declares start_frame/end_frame equal to rounded seconds×fps.
- style: the authored visual tokens needed by the coding agent.
- assets: individual id,kind,origin,rights_status,intended_use. Use permitted,unknown or pending; a public repository is not the asset permission grant.
- timeline: unit="seconds", closure_seconds=target duration, provisional boolean. A pending-voice storyboard is provisional.
- audio: status none/pending/ready; alignment not_applicable/provisional/measured/approximate; captions list. Caption data uses text,startMs,endMs,timestampMs:number|null,confidence:number|null, and preserves whitespace. Caption timestamps are milliseconds. Empty/provisional tables are not measured alignment.

engine_route contains profile,version,decision,eligibility,eligibility_basis,intended_use,exporter_available,time_unit,gaps. Profile is hyperframes/remotion_server/remotion_browser/motion_canvas/canvas_webgl/none. Exact supported pins are0.8.142/4.0.534/4.0.534/3.17.2 respectively. canvas_webgl is the source-bound P27 reel profile, with unresolved access/dependencies; it is not a new generic fallback. Decision is selected/conditional/unavailable; eligibility is eligible/unknown/blocked; intended_use is evaluation/production; exporter_available is boolean; gaps is a list of concrete dependency/eligibility gaps. Selected requires eligible use, exporter_available=true and a recorded eligibility basis. Unknown Remotion v4 production eligibility cannot become eligible due to an evaluation smoke.

For R08 only, also include `engine_prompts`, a list of two objects with `profile`, `version`, `time_unit` and `coding_prompt`: one HyperFrames profile and one Remotion server profile. Each prompt is isolated and at least500 characters. The base `engine_route` may be `none` with an unavailable exporter and concrete gaps; its base `coding_prompt` can explain the separate compilation bundle instead of combining engine APIs. This evaluation field implements the authored dual-prompt fixture; it does not select a nonexistent exporter.

coding_prompt is a detailed isolated selected/conditional engine prompt, at least500 characters by this authored structural convention. It must encode the actual director intent, facts, style, shots, timing, assets, pin/API/CLI scope, implementation/draft expectations, QA, repair and state handoff. Engine time_unit is seconds for HF/Motion Canvas and frames for Remotion; Caption fields remain milliseconds. No invented Motion Canvas headless CLI or namespace mixing is allowed. The validator detects selected API collisions; an independent reviewer must assess the prompt's full semantics and exact command/API compliance.

## States and evidence schema

states has all eleven keys, each with pass/fail/warning/not_executed/not_applicable/unknown:

plan_available, code_available, static_checked, preview_observed, encoded_artifact_available, technical_probe_passed, sample_frames_reviewed, full_motion_reviewed, audio_listened, rights_confirmed, reproducibility_scope.

A plan/prompt-only actor can honestly report plan_available=pass and the unperformed checks as not_executed; rights_confirmed remains unknown. No evidence files are needed for unexecuted states. Requested narration that is absent must not make audio_listened not_applicable or pass. Its audio QA remains warning/fail/not_executed/unknown. Listening is not_applicable only for explicitly silent intent with audio.status=none.

artifacts is a list of {kind,path}, where kind includes code,encoded_video,probe,audio. Every reported path must identify a nonempty actual file. Code/encoded/probe passing states require their actual artifacts. A probe is the retained actual ffprobe JSON, with streams/format; dimensions,fps,duration are compared to the plan. The actual video file and probe are independent from preview/build evidence. Do not create invented probe data.

evidence maps static_checked,preview_observed,sample_frames_reviewed,reproducibility_scope to lists of actual retained evidence paths when pass. Full_motion_reviewed/audio_listened passing evidence is a list of observation objects with observer,executed_at,method,scope; include actual file/time coverage, instrument/viewer and material limitations. A claim such as “should look good” is not an observation. Optional repair object for N04 has before_after_evidence with at least two actual paths plus defect/change/rerun descriptions.

qa has dimensions, mapping all nine rubric names to explicit statuses, and observation_scope describing the actual static/sample/consecutive/full/listening coverage. Dimension names: narrative_clarity,visual_consistency,pacing,animation_quality,text_legibility,factual_accuracy,audio_quality,technical_correctness,reproducibility. Pacing/animation pass requires full-motion evidence; narrated audio pass requires ready authorized actual audio and actual listening. limitations is a list. Label any encoded silent storyboard under pending narration as silent/provisional; it cannot satisfy the narrated deliverable.

## Schema fragment, not a test response

This intentionally incomplete fragment illustrates field names. It is not an expected response, cannot pass validation and must not be substituted for an actor's result:

```json
{"schema_version":"1.0","records":[{"test_id":"P01","input":"<exact input>","actor":"<actual actor>","executed_at":"<actual time>","loaded_skill_sha256":"<actual hash>","response_path":"<retained actual JSON>","output":{"plan":{},"engine_route":{},"coding_prompt":"<actual detailed prompt>","states":{},"evidence":{},"artifacts":[],"qa":{"dimensions":{},"observation_scope":[]},"limitations":[]}}]}
```

## Manual execution and review

1. Read the compiled skill and relevant cards/adapter; record loaded hash/version. Give the exact P01/P02/P03 input, preserving supplied facts and controlled pending-voice fixture.
2. Retain actual outputs and validate them with --outputs. A failing validator reports contract errors; repair actual output or clarify unsupported content, then rerun. Do not alter the checker to accept a known false claim.
3. For an actual runnable draft, retain source/lock/version,prompt,commands,logs,encoded file,actual probe and frame samples. Sample representative moments and consecutive cue-boundary frames. Record what was actually observed.
4. View the whole actual cut for pacing, animation, transitions and legibility. For requested ready narration, listen to the actual full track and inspect caption synchronization. Record observer/time/method/file/coverage. Missing narration remains unfinished rather than listening-NA.
5. Retain any actual defect, authored/admitted-scope repair and before/after evidence. Rerun affected checks. Historical P36 incidents or film-local caption/blur thresholds do not establish a present universal defect/repair.
6. Complete an independent traceability/rights/scope review and a separate activation/routing/runtime/artifact-honesty review. Preserve unsupported nulls and unknown outcomes. Report each review's real state and limits.

Package checks are independent:

```sh
python3 tests/validate_package.py --root <package-root>
```

```sh
python3 tests/validate_package.py --root <runtime-root> --manifest <explicit-hash-manifest.json>
```

The package checker verifies seven entry sections,100–300 lines,required27-file reachability,40 IDs,46 unsupported null components,16 retained bindings,20/20 partition,authored fixtures,optional exact hash manifest and no extra installed-runtime files. On the local source/audit root it also compares exact admitted component/scope/binding values with compile_views.json. Hash-manifest entries use path or relative_path,sha256,license_basis or license; distribution hash/source equality and discovery-link safety still need the actual packaging verification.
