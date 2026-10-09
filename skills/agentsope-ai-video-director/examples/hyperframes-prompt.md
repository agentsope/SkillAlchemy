# Isolated HyperFrames coding-agent prompt

Original authored prompt under C01–C07. Technical bindings are P16/P18/P19 and the current 0.8.142 branch of P20; the older Coleam blank-preview recovery is not applied to this new film. Optional P02 specification detail has unverified visual effectiveness. No creator prompt or asset is copied.

## Prompt to the coding agent

Create a project-local silent evaluation draft from this plan. Target: 15 seconds, 1080×1920, 30 fps, HyperFrames **0.8.142**. Confirm the installed exact version, Node ≥22 and local browser/FFmpeg availability; retain the lock/tree and intended-use rights basis. Do not download a logo, music or external font. The fictitious “AI 产品 / 演示占位” text demonstrates announcement layout and makes no feature claim. Product identity, features and destination link remain unknown.

Create one standalone direct-body composition with matching `data-composition-id="launch-demo"`, `data-width="1080"`, `data-height="1920"`, finite root `data-duration="15"`. The root duration must exist before scripts execute. Use a local authorized GSAP dependency and `gsap.timeline({paused:true})`; finish the whole timeline before assigning `window.__timelines[compositionId] = timeline`. If setup waits for resources, register only at the end. Timed clips have `data-start`/`data-duration` in **seconds**. Keep framework namespaces and readiness flags intact; use application-specific IDs/namespaces, and declare pending application computation through `__hf.buildReady` with unique promise keys. Duration is not resource readiness.

Build the following exact authored visual plan. Background #091018; text #F4F7FC; cyan accent #49DCE8. Title 64 px and supporting labels 32 px at this evaluation size. Use 96 px working inset as a composition token; it is not a platform safe-zone claim. Each shot contains one primary focus and a visible “演示占位” label. S1 [0,3): reveal a rounded outline card, centered portrait close-up, copy “AI 产品”. Fade its inner card from opacity 0 to 1 during the first 0.5 s and hold. S2 [3,7): move the inner card upward within its visual plane and reveal three neutral tiles with “界面示意”; use no metrics or feature names. S3 [7,11): expand an inner panel into the central area and hold “功能信息待确认”. S4 [11,15): hold “了解更多 · 链接待提供” with the card stable, leaving a final 1.5 s readable hold. These timings and style tokens are authored requirements, not distilled creative rules.

Animate inner visual elements. Let the framework own timed-clip visibility and video/audio clock; do not animate timed-clip `visibility`/`autoAlpha`, and do not manually play/seek media. Do not import Remotion frames, Sequence, React hooks or Motion Canvas generator APIs. Seek state must depend on requested time, not wall-clock timers or prior playback. Preserve all facts/unknowns/default labels and the asset ledger in the handoff.

Run these separately from the directory containing the pinned local executable, replacing project/output paths only:

```sh
./node_modules/.bin/hyperframes --version
```

```sh
./node_modules/.bin/hyperframes check <project-dir> --at 0,3,7,11,14.5 --json
```

```sh
./node_modules/.bin/hyperframes snapshot <project-dir> --at 0,3,7,11,14.5 --no-end --describe false
```

```sh
./node_modules/.bin/hyperframes preview <project-dir> --background
```

After eligibility/dependencies are established, strict evaluated export is:

```sh
./node_modules/.bin/hyperframes render <project-dir> --output <output.mp4> --fps 30 --workers 1 --no-best-effort --frames-cache-dir off
```

```sh
ffprobe -v error -show_format -show_streams -of json <output.mp4>
```

The one-worker/strict/cache-disabled choices reproduce an admitted validation profile, not a speed recommendation. Inspect actual file duration, dimensions, fps and audio absence. Inspect visible mounted frames and resource warnings; clean lint does not prove layout or complete assets. Check consecutive frames around 3,7,11 s for unintended flashes/overflow against the authored layout. Compare repeated seeks at the same times. Repair observed layout defects against the supplied shot plan, rerun affected snapshots/probes, and record the change. Do not import a film-local crown, banknote payoff, caption offset, pen treatment or source-note threshold as a new rule.

Deliver source paths, exact engine/lock information, the actual artifact path if one exists, commands/results, QA evidence and limitations. Static/frame samples establish only their coverage. Full-motion pacing requires actual viewing; no audio listening is required only because this particular evaluation draft explicitly requests silence. Report all C07 states separately. If export is unavailable, keep encoded_artifact_available not_executed and explain the concrete dependency gap.

## Binding and handoff references

Read [engine adapters](../references/engine-adapters.md) and [provenance](../references/provenance.json). P16/P18/P19/P20 retain exact documented-contract and local smoke boundaries: research docs at `2dd708e0`, npm gitHead `0b210169`; byte identity covers selected core docs only. The old 2 s silent smoke does not validate this 15 s draft, async assets, full motion or audio. [Manual review](../tests/manual-review.md) describes retained actual output records.
