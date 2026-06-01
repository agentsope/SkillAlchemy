---
name: momentic-test
description: Create, run, and maintain Momentic E2E tests and modules, which are serialized to disk as *.test.yaml and *.module.yaml files. Momentic uses fast, accurate AI agents to automate browser interactions for the purpose of testing web applications.
---

# Momentic background

## Execution model

Momentic is an end-to-end testing framework. Tests are ordered lists of
structured steps executed with Playwright and CDP.

- Interactive steps such as clicks and types use AI to resolve natural-language
  targets into concrete browser actions.
- Assertion steps can use multimodal models to evaluate page state.
- Goal-based AI actions can perform broader tasks such as "checkout with credit card".

## Cache and memory

Momentic caches resolved step metadata such as selectors, XPaths, visible text,
and coordinates so most runs avoid repeated AI calls. This is critical for speed, but
stale cache is a real debugging possibility: a step may hit the wrong element.
AI assertions may also use past-result memory to stay consistent across runs;
bad memory can explain repeated borderline failures.

Caches are scoped by git metadata, including branch. Cache writes are skipped on
protected branches, including the configured main branch, unless cache saving is
forced with `--save-cache` or the `CI` environment variable is set. Cache reads
can still happen on protected branches. Use `--disable-cache` to bypass cache
entirely.

Ways to force fresh behavior:

- Change the step description/assertion when the intent has changed; this
  changes the step identity used for cache matching. In v1, splicing a changed
  step also creates fresh internal UUIDs.
- Use `--disable-cache` for dynamic targets that should resolve fresh every run, e.g "the calendar cell for today's date".
- Preserve good previewed cache by carrying `CacheId` into splice with
  `--cache-id <CacheId>`.
- Change assertion wording and add disambiguation when previous AI memory is now misleading.

## Timing

Momentic uses "smart waiting" before targeting steps. It waits up to the
configured Smart waiting timeout, which defaults to 5 seconds, for page state to settle or the desired element to appear. Within that window, do not add manual sleeps or waits. For slower or more semantic readiness, use `waitForUrl`, text/element checks, or an AI assertion.

## Settings precedence

`momentic.config.yaml` sets project defaults, but many settings can be
overridden at the test level: browser type, viewport, locale/timezone,
geolocation, page-load timeout, smart-waiting timeout, proxy, headers, auth, extensions, etc. Always check the test's own metadata before assuming the project default applies.

## Test context

Each run has a test-scoped `env` context that persists across steps, including
modules. Later steps can read values written by earlier steps.

- v2: use `saveAs` on steps with return values.
- v1/MCP CLI strings: use `--env-key`.
- JavaScript: prefer `return` plus `saveAs` / `--env-key`; use
  `setVariable(name, value)` when setting multiple variables.
- Use `env.NAME` in JavaScript and module input expressions.
- Use `{{ env.NAME }}` in string fields. `{{ ... }}` can evaluate JavaScript,
  but do not use it inside JavaScript step source because `env` is already in
  scope there.

Module inputs are JavaScript fragments as strings. Quote literal strings and use
`env.X` for variables; they are not `{{ }}` templates.

## JavaScript context

JavaScript steps can run in `NODE` or `BROWSER`.

- `NODE`: default for API calls, data prep, OTP/email/SMS, DB queries, and
  variable writes. It has Momentic globals and preloaded libraries. `env`, `setVariable`, `email`, `sms`, `axios`, `assert`, `faker`, `moment`, `pg`, `OTPAuth`, `child_process`, etc. Check the JavaScript command docs or the Step Authoring Guide for more details
- `BROWSER`: runs in the page with `window` / `document` and page globals. It
  does not have Node-only Momentic helpers.

Keep short one-off JavaScript inline. In v2 YAML, reusable utilities and long
scripts can live in a project script file, following existing project
conventions. Prefer locations such as
`./scripts/page-utilities/auth-loader.js`. Read nearby scripts first and match their
module style, helper naming, env usage, and error style.

# Project state on disk

Tests are `*.test.yaml` files. Modules are reusable step collections stored as
`*.module.yaml` files. Test IDs are authoritative and live on the test file's
`id` field.

There are two major file formats:

- `fileType: momentic/test/v2` or `fileType: momentic/module/v2` -> **v2**.
  Direct YAML editing is preferred for high-confidence changes as it is faster.
- Missing `fileType` or any other value -> **v1**. Never edit v1 YAML
  directly; persist changes only through `momentic_test_splice_steps`.

`momentic.config.yaml` is the project root config. It stores project defaults
for agents, AI features, browser options, recording, timeouts, browser type,
file globs, and environments. See
https://momentic.ai/docs/configuration/momentic-config.md.

v2 steps can reference local files by relative path:

- Module invocations: `path: ./modules/login.module.yaml`
- JavaScript steps: `javascript: ./scripts/setup.js`
- Auth state: `authLoad: ./auth-state.json`, `authSave: ./auth-state.json`

Relative paths resolve from the YAML file containing the step, not from the
project root or importing test. Use `./...` or `../...`; do not use absolute
paths or `~`. If you move, rename, or delete a referenced file, grep for the old
path and update every reference.

v1 YAML should still be edited only through MCP. Do not use `codeFile` in v1
YAML or MCP CLI step strings; v1 JavaScript steps should carry executable code
in `code` / `--code`. Use JavaScript file references only in v2 YAML.

Do not add internal or auto-generated fields to v2 YAML.

# Before you edit

Gather only what you need:

- Test goal and user-visible success criteria.
- Start point: `baseUrl` or named environment.
- Auth requirements and required env vars.
- Risky actions that must not run twice: submit, purchase, delete, send, create.

For long tasks, inspect nearby tests and modules before authoring. Reusing an
existing module is usually better than rebuilding a common flow inline.

Ask before long-running checks, starting over from scratch, destructive actions,
or editing a shared module.

# Choose the workflow

If the user requests a specific workflow, respect it unless it is unsafe or
impossible. Otherwise, use direct v2 YAML editing when the file is v2, the
change is localized, the step sequence is known, and live UI discovery is not
required. Good examples: scaffold from a nearby pattern, reword an assertion,
adjust a target, update an env key, fix a file reference, or insert a small
known step.

Use the MCP browser-validation workflow when the file is v1 or unknown, UI state
must be discovered, locator timing is flaky, the flow is multi-step and unclear,
or the user asks to build/validate interactively ("headful mode").

Use `momentic_test_create` for new tests; search for the tool if it is not
visible. It requires `name` and either `baseUrl` or `environment`. Only pass
destination fields such as `pathSegments` when requested.
`momentic_session_start` requires an existing `testId`; it does not create
tests.

# Universal authoring rules

- Prefer natural-language element descriptions. Use selectors or
  coordinates only as a last resort for cases the AI cannot see, such as SVG
  internals, canvas, or a user-requested selector-level target.
- Prefer native Momentic steps over JavaScript. Use JS only when no native step
  expresses the behavior. JS steps can run in either the browser (client-side)
  or Node (server-side).
- Do not add navigation at the start. The session starts on the test's base URL.
- Keep assertions minimal and user-driven. Add readiness checks only when they
  are needed to make the next dependent action reliable.
- After a click/action that should navigate or materially change state, add an
  immediate validation before dependent actions. Prefer `waitForUrl` for URL
  contracts, `checkPageContains` / `checkElement...` for stable text or
  elements, and `assert` for semantic visual state.
- Do not use AI actions (`act`, `AI_ACTION`, `AI_ACTION_DYNAMIC`) unless the
  user asks or the existing test already uses one.
- Do not add optional/default fields unless needed for correctness.
- Keep the delta small. Preserve unrelated params, request bodies, env keys,
  literal values, quoting, comments, ordering, and step style.
- Do not work around real app failures. If the app is broken, data is missing,
  or a backend is down, report the failure instead of weakening the test.
- Do not reorganize `before` / `steps` / `after` or setup / main / teardown
  unless the test intent requires it.

# Working with v2 YAML

v2 is the human-editable format. Steps are compact: each step has one top-level
command key, such as `click: Submit`, or a detailed map under that key. Tests
use `before` / `steps` / `after`; modules use `steps`. Durations are always
milliseconds. No visible step/command IDs.

Direct-edit loop:

1. For a new test, create it with `momentic_test_create`, then edit the YAML in one batch instead of adding known steps one-by-one through MCP.
2. Make the smallest YAML edit. Preserve style. If you are unsure of syntax, fetch and read what is needed from https://static.momentic.ai/v2-format-reference.md.
3. Validate only if the user asked, risk warrants it, or the change needs live
   confirmation.

Common mistakes:
- Putting options beside the command instead of nesting under it.
- Using the wrong target-field name for a command.

`npx momentic lint` validates v2 schemas and file references. Lint runs
automatically before `momentic app` and `momentic run`; run it manually if you
are unsure of syntax after edits or after moving/renaming referenced files.

State refresh after disk edits:

- No active MCP session: start a fresh session when ready to validate.
- Active session plus `momentic_test_reload`: reload before `momentic_run_step`.
- Active session and no reload tool: terminate and restart the session.
- `momentic_test_get` inspects persisted state; it does not refresh an active
  session unless the tool explicitly says so.

# MCP browser-validation workflow

Use this for every v1 edit and for v2 work that needs live discovery. The tool
surface is shared; persistence differs: v1 uses splice, while v2 can use splice
or direct YAML edit plus reload.

## Discovery

- `momentic_get_artifacts()`: project context, config path, cwd, and artifact
  files for tests, modules, environments, etc. Read only what you need.
- `momentic_test_get({ testId | testPath })`: inspect persisted test state.
  Before a session, this is useful. During an active session after splicing,
  prefer the splice response or `returnTest: true`.
- `momentic_module_recommend({ userRequest })`: find reusable flows.
- `momentic_module_get({ selector })`: inspect module params, defaults, enums,
  and steps. Selector is exactly one of `{ id }`, `{ name }`, or `{ path }`.

## Sessions

- `momentic_session_start({ testId, ... })`: start browser session. It returns
  metadata, the Step Authoring Guide artifact, and Test Content with
  active-session step IDs. Required: `testId`. Call it by itself, not in
  parallel with other MCP tools. Options include env/config/project overrides,
  headful mode, and video.
- Read the Step Authoring Guide before constructing CLI-style steps.
- `momentic_run_step({ sessionId, fromStep, toStep?, targetSection?,
  resetSession? })`: run existing active-session steps. Use step IDs from Test
  Content or splice responses, never raw YAML. Use `parentStepIdChain: []` for
  top-level steps.
- If state drifts, restart with `momentic_run_step` and `resetSession: true` on
  the same `sessionId`; do not reset between every micro-edit.
- `momentic_session_terminate({ sessionId })`: terminate when done. If started
  with `video: true`, the response includes the video directory.

## Test authoring loop

Author MCP steps in checkpoint-sized chunks. Preview forward until a logical
section works, then splice that checkpoint. Good checkpoints are natural flow
boundaries such as login complete, form submitted, page deleted, etc. Avoid splicing one step at a time, unless it is highly risky and non-idempotent.

- `momentic_preview_step({ sessionId, step })`: execute one step in the browser without
  persisting. If it returns `CacheId`, include
  `--cache-id <CacheId>` when splicing that step. The response screenshot shows
  the page state after the step.
- If a preview screenshot is not enough to target, call
  `momentic_get_session_state` with `returnBrowserState: true`, then inspect the
  artifact for stable names, roles, visible text, and prominent structure to
  help craft a reliable description. Use sparingly as browser state is large.
- When the next several steps are obvious and low-risk, such as filling known
  form fields, splice them together and run that saved range instead of
  previewing each field one by one.
- `momentic_test_splice_steps({ sessionId, startIndex, deleteCount, steps,
  targetSection?, parentStepIdChain?, returnTest? })`: insert, replace, or
  delete steps and persist.
- After splicing, read the response immediately; it is the source of truth for
  inserted/deleted refs and active-session step IDs.
- If `returnTest: true`, verify the returned structure before continuing.
- If downstream steps remain, run the immediate next step to confirm the flow
  still connects.
- For non-idempotent actions such as submit, purchase, delete, send, etc.,
  avoid repeated previews. Preview the setup steps, splice the checkpoint before
  the risky action, then execute the risky saved step once only when validation
  requires it.
- For obvious adjacent low-risk steps, batch them; do not checkpoint after every
  field unless locator or page state is uncertain.
- When the requested edit is complete, ask whether to validate from the start by
  running the relevant saved range with `momentic_run_step`.

## Reading tool output

Sessions are live browser processes. Screenshots and browser states are instant snapshots. If the screenshot does not show expected state after an action, call
`momentic_get_session_state` once more; the page may still be loading.

MCP tools may return artifact links under `.momentic-mcp/...`. Read linked files
only when needed:

- UI-state text: refine targeting or debug structure.
- Screenshots: usually already returned inline as images.
- Environment files: validate `envKey`, JavaScript/API outputs, or dependent
  env values.
- `momentic_get_session_state` returns serialized UI state only with
  `returnBrowserState: true`; screenshots are returned by default.

## CLI-style step strings

`preview_step` and `splice_steps` use CLI-style strings:
`--step-type <TYPE> [options]`, e.g. `CLICK`, `TYPE`, `NAVIGATE`,
`AI_ASSERTION`, `MODULE`, `WAIT_FOR_URL`.

Examples:

- Navigate: `--step-type NAVIGATE --url "https://example.com"`
- Click: `--step-type CLICK --description "the Sign in button"`
- Type:
  `--step-type TYPE --description "Search input" --value "hello" --press-enter`
- AI assertion:
  `--step-type AI_ASSERTION --assertion "the page shows a Sign in button" --timeout-seconds 10`
- Module:
  `--step-type MODULE --module-id <id> --inputs email=env.USER_EMAIL --inputs password=env.USER_PASSWORD`

Splice example:

```json
{
  "sessionId": "SESSION_ID",
  "startIndex": 0,
  "deleteCount": 0,
  "steps": [
    "--step-type NAVIGATE --url \"https://example.com\"",
    "--step-type AI_ASSERTION --assertion \"the page shows a Sign in button\" --timeout-seconds 10 --cache-id UUID_FROM_PREVIEW"
  ],
  "targetSection": "main"
}
```

For conditionals, create the `CONDITIONAL` step with `--assertion-type` and the
matching assertion fields, then splice nested steps with
`parentStepIdChain: [conditionalStepId]`.

# Modules

Default to module-first for logical flows of 4+ steps such as login,
navigation, setup, or checkout. Call `momentic_module_recommend`, inspect strong
candidates with `momentic_module_get`, then decide module vs inline.

Modules cannot contain modules. Splicing a `MODULE` step inside a module fails.

Editing a shared module requires user confirmation. To modify a module through
MCP, replace the module step with a `MODULE` step carrying the needed metadata
flags: `--parameters`, `--parameter-enum`, `--default-parameter`,
`--module-display-name`, `--module-description`, `--module-enabled`. Keys in
`defaultParameters` and `parameterEnums` must exist in `parameters`.

Module `inputs` values are JavaScript fragments as strings. Quote string
literals, reference env as `env.X`, and respect enum constraints exactly.

# Validation strategy

- Direct v2 edit with no live validation requested: summarize changes and ask
  whether to run.
- Direct v2 edit with active session: reload if available, otherwise restart
  the session, then run the edited range.
- MCP-authored edit: preview forward, splice at logical checkpoints, then run the
  next downstream saved step or range.
- Long full-test runs and risky actions require confirmation.
- Terminate MCP sessions when done.

# Troubleshooting

## Page state and timing

- Wrong page/UI: read latest UI state or call `momentic_get_session_state`.
- Screenshot not updated: call `momentic_get_session_state` once more.
- Flaky timing: prefer `AI_ASSERTION`, `checkPageContains`, `checkElement...`,
  or `waitForUrl` over generic `WAIT`.
- Long backend job/import/upload: use an assertion or URL/text/element wait with
  an appropriate timeout instead of sleeps.
- Weird session state: use `momentic_run_step` with `resetSession: true`.

## Targeting and cache

- Element not found: inspect screenshot/UI state. If visible, improve the
  description using visible text, role, and nearby context; if absent, debug the
  prerequisite step.
- Wrong element was hit quickly or without any AI: suspect stale cache, especially when the page structure is similar to a prior run.
- Dynamic target: change the description to be stable, or disable cache for that
  step.
- Playwright stability failure: a target can be found but still not be
  actionable because it is hidden, detached, outside the viewport, covered, or
  animating. Prefer fixing page state when possible. Use `--force` only for that
  step when bypassing actionability is acceptable, or enable project-wide visual
  actions if coordinate-based interaction is the right tradeoff.
- Visual actions are enabled in project browser settings with
  `visualActions: true`. Momentic interacts by X/Y coordinates and tries to
  preserve element identity best-effort instead of hard-failing like Playwright
  actionability checks.
- Quoted text: quoted substrings in descriptions are treated literally by
  Momentic AI. Use quotes only when that exact text must appear on screen or in
  the element's accessible name; omit quotes for semantic matching.

## AI assertion performance

- Ambiguous assertion: make the expected visual/text condition concrete. Include
  the relevant page region, object, count, or state.
- Literal text mismatch: quoted strings are treated as text that must appear on
  screen. Remove quotes when semantic matching is intended. Describe the purpose
  of elements when possible rather than specific text or labels.
- Out-of-viewport: visual conditions like color or shape can only be evaluated
  if the element is in the viewport. Use scroll/hover setup.
- Visually subtle condition: `AI_ASSERTION` supports VISION_ONLY mode which has
  better visual reasoning.
- Repeated bad verdict: reword the assertion so the intended condition is
  clearer and old memory no longer applies.
- Transient conditions: AI checks retry multiple times over the configured
  timeout but each attempt is an instantaneous snapshot. As such, extremely fast
  changes like toasts that appear and vanish in 1 second can be missed. Also,
  there is no ability to evaluate changes over time ("the screen is darker than
  before"). Prefer crafting assertions for stable final state; if necessary
  client-side JavaScript observers can be used.

## Format and data

- v2 load/run failure: run `npx momentic lint <path>`; broken relative file
  references are common after moves.
- Module failure: re-check required params, defaults, enums, and JS-fragment
  input syntax with `momentic_module_get`.
- Env value missing: confirm the producing step used `saveAs` / `--env-key` or
  `setVariable`, and that the consuming syntax is `env.X` vs `{{ env.X }}`.
- JavaScript failure: confirm the environment. Browser JS cannot use Node
  helpers; Node JS cannot read live DOM globals.

After about three attempts on the same problem, stop and ask the user for a
direction.

# Decision cheat sheet

- Known v2 sequence: direct YAML edit.
- v1 or unknown UI state: MCP preview, splice, validate.
- Need the right step index: use Test Content, splice refs, or `returnTest`;
  never raw YAML step IDs.
- Need the browser at step N: run once from start/setup to N-1, then keep using
  the same session.
- Single new step idea: `momentic_preview_step`.
- Persist validated MCP steps: `momentic_test_splice_steps`.
- Clean restart: `momentic_run_step` with `resetSession: true`.
- Validate direct v2 edit: `momentic_test_reload` if active, else fresh session.
