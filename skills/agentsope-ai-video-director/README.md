# agentsope-ai-video-director

从一句话生成可执行导演方案、独立引擎编码提示，并在工具可用时实施、渲染、检查和修订视频。默认输出真实达到的状态；方案、代码、编码文件、看过完整动态和听过声音是不同结果。

Use for product/SaaS launches, vertical social clips, data/technology explainers, kinetic typography/brand, cinematic visual shorts, website/GitHub/docs videos and voice-led knowledge videos. These seven application guides are authored package structures. Their research support varies; cinematic coverage is limited and diffusion procedures have not been distilled.

Start with [SKILL.md](SKILL.md). Example: “用 15 秒展示一个虚构任务管理产品的三步整理流程，用原创图形，先做可渲染草稿。” Critical product claims, assets and rights stay pending; reversible aesthetic defaults are declared assumptions. The agent continues authorized provisional work and creates actual code/video where an eligible exporter exists.

## Project-local installation

Place this runtime directory at `<project>/dist/agentsope-ai-video-director/` (or another project-local location). Link only within that project:

```sh
mkdir -p .agents/skills .claude/skills
ln -s ../../dist/agentsope-ai-video-director .agents/skills/agentsope-ai-video-director
ln -s ../../dist/agentsope-ai-video-director .claude/skills/agentsope-ai-video-director
```

If discovery links already exist, inspect their target before replacing them. This guide does not install engines or global skills. Engine dependencies belong to the video project, and must be probed/version-matched before rendering.

## Engines and verification limits

HyperFrames 0.8.142 uses HTML composition seconds and completed paused timeline registration. Remotion 4.0.534 uses deterministic frame state, with separate Node/server and browser-compositor adapters. Motion Canvas released 3.17.2 uses seconds in generators and an editor-driven registered exporter; no headless CLI is claimed. Canvas/WebGL remains a source-local documented renderer note, not a universal fallback. Read [engine adapters](references/engine-adapters.md).

Research-time original HyperFrames and Remotion silent 2-second smoke videos were encoded, probed and sampled. They do not validate voice, all media/fonts, full pacing or listening. Motion Canvas TypeScript/Vite/server checks passed; actual video export/UI/audio remain unexecuted. Browser Remotion export is also unexecuted. Remotion production eligibility remains user/use-specific under pinned v4 terms. The inspected cached Motion Canvas exporter FFmpeg binary had nonfree build terms and is excluded from distribution. Exact release/main revision and binary terms must be checked separately.

## Examples and checks

All examples are original synthetic demonstrations, never counted research cases; their represented video checks remain unexecuted until an actor performs them.

- [Sentence to plan](examples/sentence-to-director-plan.md)
- [Detailed HyperFrames prompt](examples/hyperframes-prompt.md)
- [Detailed Remotion prompt](examples/remotion-prompt.md)
- [15s product application](examples/product-launch.md)
- [30s data application](examples/data-explainer.md)
- [60s narrated docs application](examples/narrated-docs.md)
- [Sentence fixtures](tests/sentence-inputs.json), [routing fixtures](tests/engine-routing.json), [missing/error fixtures](tests/missing-and-errors.json)
- [Quality checklist](tests/quality-checklist.md), [manual review and output contract](tests/manual-review.md)
- [Package validator](tests/validate_package.py), [actual-output validator](tests/validate_outputs.py)

Run from any working directory using the actual paths:

```sh
python3 <skill-dir>/tests/validate_package.py
python3 <skill-dir>/tests/validate_outputs.py --outputs <actual-agent-outputs.json>
```

These checks establish structure and recorded contract compliance, not full audiovisual quality. Validators do not produce canned agent answers. Retain real agent outputs, commands and observed checks separately; label unexecuted tests honestly.

## Reference index

- [Prompt patterns](references/prompt-patterns.md), [director playbook](references/director-playbook.md), [seven video types](references/video-types.md)
- [Quality rubric](references/quality-rubric.md), [40 operation cards](references/sop_models.md)
- [Sources and rights](references/sources.md), [42 creative case ledger](references/case-studies.md)
- [Research coverage](references/research_notes.md), [rule/finding/source provenance](references/provenance.json)
- [Metadata and explicit runtime manifest](skill.json), [original-content MIT license](LICENSE)

The runtime manifest has 27 authored files. Local research reports, caches, tooling, Git history, installed dependencies/binaries and exemplar copies are audit material excluded from installation/archive. Every important operation traces to an admitted P rule, exact scope, finding and source/version. C01–C09 are separately declared authored contracts. General admission does not mean universal creative effectiveness; P02/P05/P06/P09 are optional author suggestions awaiting empirical validation.

## Executed package evaluation — additive release record

A fresh delegated worker loaded this compiled skill and produced 14 retained actual responses: the three sentence requests (P01/P02/P03), five routing cases and six missing/error cases. The strengthened actual-output validator passed the final retained response set (exit 0). The first failure, exact-fixture clarification and follow-up reruns remain in the separate local audit. These are delegated instruction-workflow evaluations, not external Claude Code or Codex CLI integration tests. The authored fixture definitions retain their original `not_executed` labels; the executed responses and reports are recorded independently.

The root also implemented and checked an independent original B01 HyperFrames benchmark: four shots, 15 seconds, 1080×1920, 30 fps and 450 decoded frames; H.264/yuv420p, silent MP4, 1,410,286 bytes. It differs from the worker’s five-shot 720×1280 P01 response and is excluded from research-case counts. Its actual technical probe passed. Browser checks reported zero runtime/layout errors and 42/42 contrast checks, with five structural warnings and motion audit disabled. Observed implementation, font and shot-boundary defects were fixed and rechecked using before/after evidence. The root inspected eight representative frames and twelve boundary frames; four ordered/shuffled seek samples had identical SHA-256 hashes.

Full-motion viewing remains **not_executed**. Audio listening is **not_applicable only for this explicitly silent benchmark**; it does not clear pending narration in P03 or the narrated-docs application. Final production rights and product claims remain unknown, and `publish_ready` is false. The encoded draft, frames, logs and reviews remain in the separate local audit, outside the runtime archive. Static/technical/frame evidence establishes only its actual coverage and does not certify audiovisual or production completion.

Two independent reviews completed: evidence/rights/scope passed with limitations, and activation/routing/runtime review passed with nonblocking limits. The route review strengthened all authored route/error contracts and the R08 separate-engine Prompt bundle. Twenty-one checker mutation probes were executed and rejected their deliberately invalid contracts; they are validator checks, not actor responses. The historical research observations above remain unchanged.
