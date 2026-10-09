# Isolated Remotion server coding-agent prompt

Original authored application of C01–C07 plus P21/P22/P24/P37/P40. This prompt targets **Remotion 4.0.534 server rendering**. The browser compositor is a separate adapter, with unexecuted browser export and its own supported subset. No HyperFrames metadata or Motion Canvas generators belong here.

## Prompt to the coding agent

Build a project-local synthetic data explainer: 30 s, 1920×1080, 30 fps, 900 frames, last frame 899. Data supplied for this demo: starting revenue 40, ending revenue 55. Units, periods, source and cause are unknown. Labels must say “用户提供的演示数据；单位、时期与来源待确认”. No accuracy/causal claim may be invented. Target audience is a general viewer, and horizontal web presentation is a labeled package assumption. Silent draft is an explicit evaluation assumption. Use original vector marks, system-rendered text and no third-party media.

Before production, record the exact subject/use eligibility basis under the pinned v4 license. Individual/nonprofit/for-profit with at most three employees/noncommercial evaluation conditions differ from other for-profit production uses. Unknown eligibility stays unknown and prevents a production render route from being declared selected. No Company License purchase is authorized. The local noncommercial smoke establishes no user production permission. Keep hosted services, codecs, media rights and server/client telemetry scopes separate; do not substitute announced v5 requirements for v4.

Use version-matched packages and `registerRoot(Root)`. Register a `Composition` with id `DataDemo`, component, fps 30, width 1920, height 1080 and `durationInFrames=900`. Derive visible state from zero-indexed `useCurrentFrame()`. `Sequence` intervals are [from,from+duration), and each child sees a local frame. Explicitly pass absolute frame only if needed by the authored design. Use `spring({frame,fps,...})` with fps 30 and `interpolate` with explicit left/right clamp where the visual requires bounded values. Do not use wall-clock timers or mutable prior-tab state. Concurrency 1 is not a remedy for wall-clock animation.

Implement five shots: S1 [0,120) title “收入的两个数值” on near-white #F5F6F8 with navy #182C47; establish the two supplied revenue values without animation of their digits. S2 [120,300) show a bar for 起点 fixed at 40 on a clearly labeled 0–60 illustrative display scale; animate geometry, keep its printed value fixed. S3 [300,510) reveal the 终点 bar fixed at 55 beside the first, with aligned baseline and direct starting/ending labels. S4 [510,720) show the authored arithmetic “55 − 40 = 15” and “差值 15（原单位） · 增幅 37.5%（计算）”; these are computations from supplied values, not a cause or newly sourced measurement. S5 [720,900) hold both bars and the provenance/unknown note. Title 68 px, direct labels 44 px, source note 32 px, 100 px working inset are authored design tokens. Use straight cuts/short inner-mark opacity ramps; keep the note readable in each relevant shot and test actual overflow. No universal reading threshold is asserted.

For asynchronous resources on this server path allocate a stable lazy `delayRender` handle with `useState`; call `continueRender(handle)` on completion or `cancelRender(error)` on failure. Do not allocate on every rerender. Load any authorized font before measuring text. Default readiness timeout at this pin is 30 s. The draft has no requested audio; if later requested, import `Audio` from `@remotion/media`, use `staticFile` for authorized local audio, and keep `from`, `trimBefore`, `durationInFrames` in frames. `durationInFrames` selects source frames and occupies durationInFrames/playbackRate parent frames. `Caption` from `@remotion/captions` is plain data with `text`, `startMs`, `endMs`, `timestampMs:number|null`, `confidence:number|null`; preserve whitespace. Captions use milliseconds, not frame counts, and creating data is not transcription or alignment.

Use the admitted local server commands as separate invocations after verifying executable/browser paths:

```sh
./node_modules/.bin/remotion versions
```

```sh
./node_modules/.bin/remotion studio <entry.tsx> --port=<port>
```

```sh
./node_modules/.bin/remotion still <entry.tsx> DataDemo <output.png> --frame=300 --image-format=png --browser-executable=<chrome-path>
```

```sh
./node_modules/.bin/remotion render <entry.tsx> DataDemo <output.mp4> --codec=h264 --concurrency=2 --browser-executable=<chrome-path>
```

```sh
ffprobe -v error -show_format -show_streams -of json <output.mp4>
```

Concurrency 2 is a reproduced smoke profile, not a performance optimum. The equivalent documented server API route is bundle/serve URL → selectComposition → renderMedia; do not replace it with `renderMediaOnWeb`. Compare repeated and reordered still capture at frames 120,300,510,720 within the actual environment. Verify frames around those transitions and final frame 899, numbers/labels, chart baseline, source note, dimensions/duration/fps and actual audio state. A deliberate empty starting spring frame requires judging its authored purpose; it is not automatically an export defect. Fix observed geometry/text defects against this plan, rerun affected checks and retain changes/logs.

Return code, plan, detailed prompt, command log and actual artifact/probe only when they exist. Report eleven C07 states separately and nine QA dimensions. A build or still does not prove the whole video; full-motion/listening stays not_executed until observed. Server licenseKey/success telemetry differs from browser completed/failed telemetry; do not hide that distinction. If tools or eligibility prevent export, deliver plan/prompt/code and the concrete gap, with encoding/probe states not_executed.

## References

[P21/P22/P24/P37/P40 binding cards](../references/sop_models.md), [adapter profiles](../references/engine-adapters.md), [source provenance](../references/provenance.json), [data application](data-explainer.md). Scope is 4.0.534 / `4d9ff70e`; the researched 2 s silent server smoke and stills do not validate this new cut, its audio or its full motion.
