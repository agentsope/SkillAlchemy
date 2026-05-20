---
name: agentsop-session-state-hygiene
version: 0.1.0
description: |
  Decision protocol for managing the context/session state of an AI coding tool:
  when to /clear, when to keep context, and how to detect "context bleed" — the
  failure mode where stale conversation history biases the model against the
  current task. Surfaces a discipline that Aider (/clear), Claude Code (/clear),
  CrewAI (memory=False, re-instantiate), and LangGraph (new thread_id, subgraph
  isolation) all encode separately but none name as a skill.
phase: D
tier: common
frequency: daily
audience: coder-agents and human engineers who run multi-turn LLM coding sessions
source: aider-sop, crewai-sop, langgraph-sop (local) + vendor docs
---

# Session-State Hygiene · SOP

> One line: **context is signal; stale context is noise; clearing restores
> signal.** A coding session is a sliding window of evidence. Early in a task
> the window is pure signal. The longer it runs, the more dead ends, abandoned
> plans, and superseded files accumulate — and at some point yesterday's good
> context becomes today's bad bias. This skill is the discipline of noticing
> that moment and acting on it with the smallest correct cut.

> Source posture: every framework-specific claim is cited inline as
> `[tool/topic]`. Resolve tags against `references/R1-source-evidence.md` (full
> URLs) and `references/R2-tool-commands.md` (copy-pastable commands).

---

## 1. 何时激活 (When to Activate)

Activate this skill the moment **any** of these fire — they are the symptoms of
context bleed, not vague unease:

- **Topic shift inside a session.** You finish feature A and start unrelated
  bug B in the same window/REPL/thread. The A-history is now pure noise for B.
- **Length / window warning.** The tool reports the context window is N% full,
  or Aider's `/tokens` crosses **~25k** — the empirically observed point where
  "most models start to become distracted and become less likely to conform to
  their system prompt" `[aider/edit-errors]`.
- **Weird behavior** — the tell-tale signs of bleed:
  - The model **repeats a mistake** you already corrected ("don't use
    `requests`" → it uses `requests` again).
  - It **references a file or decision you already removed / dropped**.
  - It **obeys an older instruction over the newest one** (it conforms to turn
    3 but ignores turn 30).
  - Edit-format errors climb (Aider "SEARCH block not found" recurs)
    `[aider/edit-errors]`.

> **The activation trap to avoid:** when behavior gets weird, the reflex is to
> rephrase the prompt, retry, or swap the model. If the *history* is polluted,
> none of those help — you are arguing with a model that is reading stale
> evidence. Activate this skill **before** reaching for a prompt rewrite.

Do **not** activate for: a single LLM call, a one-shot RAG query, or a brand new
session with <25k tokens that is behaving correctly. Hygiene on a clean window is
just superstition — see §6.

---

## 2. 核心心智模型 (Core Mental Model)

**Context is signal; stale context is noise; clearing restores signal.**

Three load-bearing ideas ride this axiom:

### 2.1 The session window is evidence, and evidence decays

Every turn you add to a session is evidence the model reasons over. Good
evidence (the current goal, the relevant files, the last working diff) raises
signal. Stale evidence (a failed approach you abandoned, a 5k-token search dump
you no longer need, a file you dropped) raises noise. The signal-to-noise ratio
of the window — not its absolute size — is what governs output quality. A 10k
window of pure noise is worse than a 30k window of pure signal.

### 2.2 There is a measured distraction threshold

Aider's tooling is built around a hard, published number: above **~25k tokens**
"most models start to become distracted" `[aider/edit-errors]`. No other
framework publishes a number, but the heuristic transfers: treat ~25k as the
point where you should be *actively* shedding context, not passively letting it
grow. This is why `/tokens` exists and why it is the first move in Aider's
edit-error remediation, *before* swapping model or edit format `[aider/edit-errors]`.

### 2.3 Clearing is a cut, and cuts have a size

"Clear the context" is not one operation — it is a family ordered by blast
radius. The skill is choosing the *smallest* cut that removes the noise:

```
        smallest cut                                      largest cut
   ┌───────────────┬────────────────┬───────────────┬──────────────────┐
   │ drop one item │ trim history   │ clear history  │ fresh session /  │
   │ (a file, a    │ (keep last N   │ (keep files,   │ new thread_id    │
   │  message)     │  messages)     │  drop history) │ (zero carry-over)│
   └───────────────┴────────────────┴───────────────┴──────────────────┘
     OP-004 partial   OP-004 partial   OP-002 save+clear   OP-003 fresh
```

Reaching for "fresh session" when a single `/drop` would do is as wrong as never
clearing at all. Match the cut to the noise.

### 2.4 The window is not the only state

A subtle trap: "session state" is broader than the visible transcript. CrewAI's
`memory=True` keeps a **separate persistent store** (LanceDB by default) that a
`Crew()` re-instantiation does **not** wipe `[crewai/memory]`. LangGraph's state
lives in a **checkpointer** keyed by `thread_id` — a new `thread_id` is clean,
but reusing the old one resumes from the last checkpoint `[langgraph/persistence]`.
"I cleared the chat but it still remembers" almost always means a persistent
store you didn't clear (§6, AP-005).

---

## 3. SOP 工作流 (Standard Operating Procedure)

The flow is four steps: **recognize → save what's worth → clear → restart
focused.** Walk it top-down; each step has a gate.

### Step 1 — Recognize (don't act yet)

Gate: *name the symptom in one line* before touching anything. "The model is
still using the JWT approach we abandoned." "Token count is 38k and edits are
failing." Naming forces you to identify the **single offending source** —
stale history, an oversized item, or the wrong file set — which then selects the
cut size. If you cannot name a symptom, you do not have bleed; do not clear
(§6, AP-002). This is OP-001.

### Step 2 — Save what's worth keeping (before any clear)

Gate: *is there a durable artifact in this session you'd hate to retype?* A
decision, a file list, a working plan, a passing-test state. If yes,
**externalize it to something that survives the clear**:

- **Code** → it's already safe if committed (`git commit`); commit before you clear.
- **Decisions / conventions** → write to `CONVENTIONS.md` (Aider re-loads it via
  `--read`) or a scratch note `[aider/conventions]`.
- **The plan / state-of-the-world** → ask the model for a one-paragraph summary
  (decisions made, files touched, tests passing, open questions), copy it.

The keepers go to disk/git/clipboard — **never** left only in the volatile
window you are about to wipe. This is OP-002.

> If the bug you're hunting depends on the *exact* phrasing the model used three
> turns ago, a summary is too lossy — save the raw transcript instead. But if you
> need the raw transcript, ask whether you actually needed to clear.

### Step 3 — Clear (smallest correct cut)

Pick the cut from §2.3 by blast radius:

| Situation | Cut | Command |
|---|---|---|
| One bloated item (big file, old dump) | **partial** (OP-004) | Aider `/drop <file>`; LangGraph `update_state(messages=trimmed)` |
| Same topic, history polluted | **save + clear** (OP-002) | Aider `/clear`; Claude Code `/clear`; CrewAI re-instantiate `Crew` |
| Topic fully changed, nothing carries | **fresh** (OP-003) | Aider `/reset` or relaunch; LangGraph new `thread_id`; web "New chat" |
| Noisy sub-investigation pollutes main | **isolate** (OP-006) | LangGraph subgraph; separate CrewAI Crew; second Aider window |
| Debugging, need reproducible runs | **memory off** (OP-007) | CrewAI `memory=False`; LangGraph `InMemorySaver` / throwaway thread |

For code tools, the working tree on disk is **never** touched by a chat clear —
`/clear` resets the transcript, not your files `[claude-code/slash]` `[aider/commands]`.

### Step 4 — Restart focused

Gate: *the first message of the new context is a focused goal statement, not a
data dump.* Open with the saved one-paragraph summary (OP-002) plus the single
current objective. Do **not** paste the old transcript back — that recreates the
pollution with extra steps (§6, AP-003). A clean window seeded with distilled
state is the entire payoff of clearing.

---

## 4. 操作模型 (Operation Models)

Each operation: **Trigger → Action → Output → Evidence.** Full machine-readable
form in `intermediate/operation_candidates.json`; commands in `references/R2`.

### OP-001 · Detect context bleed
- **Trigger**: Any §1 symptom — topic shift, length warning, or weird behavior
  (repeats corrected mistake / cites removed item / obeys old over new).
- **Action**: Stop. Do not edit the prompt, retry, or swap model. Name the
  symptom in one line and identify the single offending source.
- **Output**: A named symptom and a chosen cut (OP-002/003/004/006).
- **Evidence**: `[aider/edit-errors]` (25k distraction); `[langgraph/persistence]`.

### OP-002 · Save-and-clear (same topic, polluted history)
- **Trigger**: Continue the same topic but history is full of dead ends.
- **Action**: (1) Have the model summarize decisions + state in one paragraph.
  (2) Copy it to disk/clipboard. (3) Clear: Aider `/clear`, Claude Code
  `/clear`, CrewAI re-instantiate `Crew`, LangGraph new `thread_id`, web "New
  chat". (4) Paste the summary as the first message.
- **Output**: Fresh history seeded with distilled state; files/working tree untouched.
- **Evidence**: `[aider/commands]` (`/clear` preserves `/add`-ed files).

### OP-003 · Fresh thread (topic fully changed)
- **Trigger**: New feature/bug/task AND nothing from the old session is needed.
- **Action**: Start a genuinely new session. Aider: relaunch or `/reset`. Claude
  Code: `/clear` or exit. CrewAI: a **new** `Crew()` instance (do not reuse).
  LangGraph: a fresh `thread_id` (do not reuse the old uuid). Web: New chat.
- **Output**: Zero bleed; cheapest possible window for the new task.
- **Evidence**: `[crewai/memory]`; `[langgraph/persistence]` (different `thread_id` = different conversation).

### OP-004 · Partial clear (drop a subset, keep continuity)
- **Trigger**: History is mostly good; one item (a big paste, a stale tool
  result, an unneeded file) is the noise.
- **Action**: Surgical removal, not a full clear. Aider: `/drop <file>` + confirm
  with `/tokens`. LangGraph: `update_state(config, {"messages": trimmed})` or
  `RemoveMessage`. CrewAI: trim a Task's `context=[...]` to only the needed
  upstream tasks.
- **Output**: Reduced footprint, conversational continuity preserved.
- **Evidence**: `[aider/commands]` (`/drop`, `/tokens`); `[langgraph/manage-history]`.

### OP-005 · Fresh thread vs reuse (where to put the seam)
- **Trigger**: Starting a related-but-new subtask; unsure whether to continue.
- **Action**: Default to a fresh thread when the new subtask shares **<30%** of
  relevant context with the old one. Reuse only when the new task strictly
  builds on the live state (next step of the same diff).
- **Output**: A session boundary placed at the natural task seam.
- **Evidence**: `[langgraph/persistence]`; `[crewai/memory]`.

### OP-006 · Isolate a noisy sub-task in a sub-context
- **Trigger**: A noisy sub-investigation (debugging, big search, exploratory
  dump) would pollute the main session if run inline.
- **Action**: Run it in an isolated context and return only the conclusion.
  LangGraph: a **subgraph** with its own state schema. CrewAI: a separate `Crew`
  with `memory=False`, return `result.raw`. Aider: a second window whose only
  output back to the main task is a committed diff or a note.
- **Output**: Main session receives a one-line conclusion, not the full trace.
- **Evidence**: `[langgraph/subgraphs]` (child state isolated to shared keys);
  `[crewai/memory]`.

### OP-007 · Memory off during debug
- **Trigger**: Debugging or evaluating behavior; you need reproducible traces.
- **Action**: Turn off persistent/auto memory so each run starts from a known
  state. CrewAI: `memory=False` (and wipe `~/.crewai/storage/` if `memory=True`
  was used). LangGraph: `InMemorySaver` or a throwaway `thread_id`. Aider:
  `/clear` before each repro.
- **Output**: Deterministic starting state; runs become comparable.
- **Evidence**: `[crewai/memory]` (memory runs extra LLM calls, hard to trace);
  `[langgraph/persistence]`.

### OP-008 · Inspect before you cut
- **Trigger**: You suspect bloat but haven't confirmed the source.
- **Action**: Look first. Aider: `/tokens`, `/ls`, `/map`. Claude Code:
  `/context`. LangGraph: `len(state["messages"])` / `get_state`. CrewAI: read the
  LangSmith/MLflow trace.
- **Output**: The offending source identified, so OP-002/004 cut the right thing.
- **Evidence**: `[aider/commands]`; `[claude-code/slash]`; `[langgraph/manage-history]`.

### OP-009 · TTL-sweep stale sessions
- **Trigger**: Long-lived setups accumulate abandoned threads / huge old stores.
- **Action**: Expire sessions past a threshold (e.g. 24h). LangGraph: a TTL sweep
  on the checkpointer for interrupted-but-never-resumed threads. CrewAI: clear
  the long-term store. Aider: end sessions; don't keep one REPL alive for days.
- **Output**: Bounded state growth; no zombie context resurfacing.
- **Evidence**: `[langgraph/hitl]` (without a sweep, "state is held in the
  checkpointer indefinitely").

---

## 5. 困境决策案例 (Dilemma Cases)

### Case 1 · "The fix depends on a prior file — but bleed is getting worse"

**困境**: You're 20 turns into refactoring `auth.py`. The model now mixes in a
JWT approach you explicitly abandoned at turn 8, *and* the correct new code
genuinely depends on the `session.py` changes made at turn 5. Clearing risks
losing the dependency; not clearing keeps the bleed.

**约束**:
- The `session.py` changes are load-bearing for the current edit.
- The abandoned JWT history is actively misleading the model.
- You don't want to retype the whole refactor plan.

**决策步骤**:
1. **Recognize** (OP-001): name it — "model resurrects abandoned JWT; correct
   edit depends on the turn-5 `session.py` change."
2. **Make the dependency durable, not conversational** (OP-002): the turn-5
   change is *code* — commit it (`git commit`). Now it lives in the working tree,
   not the volatile transcript. The model will see the file content after a
   `/clear` because `/clear` keeps `/add`-ed files `[aider/commands]`.
3. **Prefer the smallest cut**: if only the JWT turns are noise, OP-004 partial —
   LangGraph `update_state` to drop those messages; Aider has no message-level
   drop, so escalate to OP-002.
4. **Save + clear** (OP-002): one-paragraph summary ("refactoring `auth.py` to
   use the new `session.py` API committed at <sha>; do NOT use JWT"), then
   `/clear`, then paste the summary.
5. **Restart focused**: the new window has the committed file + the summary —
   the dependency survives, the bleed is gone.

**结果**: The prior-file dependency is preserved *through git*, not through chat
history — so clearing is safe. The general rule: **if the thing you fear losing
can be made durable (committed, written to a note), clearing is always safe.**

**可提取的操作**: OP-002 + OP-001. Never let "I might need it" keep a polluted
window alive — externalize the keeper, then cut freely.

---

### Case 2 · "Long task is 80% done — restart clean or push through?"

**困境**: A multi-step migration is 80% complete. The window is at 34k tokens
(past the ~25k distraction line `[aider/edit-errors]`), edits are starting to
fail intermittently, and the model occasionally references a step it already
finished. Do you restart (risking the 80% momentum) or push through the last 20%?

**约束**:
- Restarting costs a re-summary + reload; pushing through risks the failing
  edits corrupting the near-done work.
- The done 80% is mostly *committed code* already.
- The remaining 20% is well-defined.

**决策步骤**:
1. **Recognize** (OP-001): "34k tokens, intermittent edit failures, model
   re-references finished steps" — this is bleed at the distraction threshold,
   not bad luck.
2. **Audit the keepers** (OP-008 → OP-002): is the 80% *durable*? If committed,
   the momentum lives in git, not the window — restarting loses almost nothing.
   If uncommitted, **commit first**.
3. **Decision rule on the seam** (OP-005): the remaining 20% shares little
   relevant context with the noisy 80%-of-failed-attempts history (the *code* is
   the shared part, and that's on disk). Shared *conversational* context is low →
   favor a fresh window.
4. **Save + clear** (OP-002): summarize the migration state ("steps 1-8 done,
   committed at <sha>; remaining: steps 9-10 = update callers + delete shim"),
   `/clear`, paste, finish the last 20% in clean signal.
5. **Counter-case**: if the last 20% is a *single small edit* and tokens are only
   slightly over, the cheaper move is OP-004 — `/drop` the unused files and push
   through. Don't pay the restart tax for one trivial step.

**结果**: At 80% with committed work, a clean restart usually *wins* — you finish
the hardest 20% on full signal instead of fighting a distracted model. The
threshold is whether the done work is durable; if it is, the sunk-cost feeling of
the long session is an illusion.

**可提取的操作**: OP-005 + OP-002. "Almost done" is not a reason to push through a
distracted window; it's a reason to make the done part durable and finish clean.

---

### Case 3 · "I cleared it but the model still remembers" (the hidden-store trap)

**困境**: A CrewAI debugging session: you re-instantiated the `Crew()` object
between runs, but the agent still recalls a fact from a previous kickoff that you
thought you'd wiped.

**约束**: You need reproducible runs; the lingering recall makes traces unreadable.

**决策步骤**:
1. **Recognize** (OP-001): the symptom is "cleared but remembers" → the state is
   not in the window you cleared. It's in a **persistent store** (§2.4).
2. CrewAI `memory=True` keeps a separate LanceDB store under `~/.crewai/` that a
   `Crew()` re-instantiation does **not** touch `[crewai/memory]`.
3. **Memory off for debug** (OP-007): set `memory=False`, and if a prior run used
   `memory=True`, wipe the store: `rm -rf ~/.crewai/storage/`.
4. Generalize: LangGraph reusing a `thread_id` resumes from a checkpoint — use a
   fresh `thread_id` (OP-003). Web UIs with cross-chat memory: "New chat" does
   not clear it; clear it in Settings `[langgraph/persistence]`.

**结果**: Deterministic runs once the *actual* state location is cleared.

**可提取的操作**: OP-007. Before concluding "clearing doesn't work," ask **which**
state you cleared — the transcript or the persistent store.

---

## 6. 反模式与边界 (Anti-Patterns & Boundaries)

| # | Anti-pattern | Symptom | Fix |
|---|---|---|---|
| AP-001 | **Never-clear marathon** | Hours-long session; model "forgets" instructions, invents files dropped 50 turns ago | Clear on any topic shift OR every ~25k tokens (OP-002). `/clear` is a stop-the-line tool, not a panic button `[aider/edit-errors]` |
| AP-002 | **Reflexive clear-every-message** | Clearing so often the model loses useful continuity — re-asks answered questions, forgets which files are in scope | Clear only on a *named* symptom (OP-001). "Feels off" is not a trigger |
| AP-003 | **Dump the whole old transcript back in** | You `/clear` then paste 50 messages back — pollution recreated with extra steps | Paste a *summary* (OP-002), not raw history. If you truly need the raw history, you didn't need to clear |
| AP-004 | **Clear instead of fixing the real bug** | `/clear` after every failed edit, but the bug is in the prompt or model | If the failure repeats *after* a clean clear, the history wasn't the cause — fix the prompt/model |
| AP-005 | **Forget memory is on (hidden store)** | "Cleared" the session but the agent still recalls a fact | The persistent store survived (§2.4, Case 3). `memory=False` in debug, or wipe the store `[crewai/memory]` |
| AP-006 | **Keep huge old dumps "just in case"** | A 10k-token log/file sits in context for 30 turns "in case it's useful" | If unused for several turns, `/drop` it (OP-004). It can be re-added in seconds; the noise tax is paid every turn |
| AP-007 | **Buy a bigger window instead of clearing** | Moving to a 1M-context model to avoid `/clear` | A bigger window doesn't *remove* stale signal — it just lets more noise accumulate. Signal-to-noise, not size, governs quality |

**Hard boundaries — when this skill does *not* apply:**
- A single LLM call or one-shot RAG query: no session to keep hygienic.
- A clean window (<~25k, behaving correctly, on-topic): clearing is superstition.
- When the real problem is the prompt or the model: clearing the history is
  treating a symptom (AP-004). Confirm the bug isn't in the live turn first.

---

## 7. 跨框架对照 (Cross-Framework Reference)

All surveyed coding tools expose the same primitive under different names. The
convergence is itself the argument that this SOP deserves to be a surfaced skill.

| Need | Aider | Claude Code | CrewAI | LangGraph | ChatGPT/Gemini web |
|---|---|---|---|---|---|
| Inspect context size | `/tokens` | `/context` | LangSmith / MLflow trace | `len(state["messages"])` | (UI hint) |
| Clear chat, keep files | `/clear` | `/clear` | re-instantiate `Crew()` | new `thread_id` | New chat |
| Hard reset everything | `/reset` | exit CLI | new process + wipe store | new `thread_id` | New chat (+ clear memory in Settings) |
| Partial clear (drop subset) | `/drop <files>` | n/a | trim Task `context=[...]` | `update_state({"messages":...})` / `RemoveMessage` | n/a |
| Isolate a sub-task | second window | sub-process | separate `Crew`, `memory=False` | subgraph w/ own schema | New chat |
| Memory off (debug) | `/clear` per repro | `/clear` per repro | `memory=False` | `InMemorySaver` / throwaway thread | n/a |

Concrete, copy-pastable commands per tool are in `references/R2-tool-commands.md`.

### The four primitives, side by side

- **Aider** `[aider/commands]`: file-level granularity. `/clear` wipes chat but
  keeps the `/add`-ed working set (so the model still knows *what* it can edit);
  `/reset` wipes both. `/drop` is the partial cut; `/tokens` is the gauge. The
  cleanest published distraction threshold (~25k) lives here `[aider/edit-errors]`.
- **Claude Code** `[claude-code/slash]`: `/clear` resets the in-memory transcript;
  files on disk are the durable state and are never touched. `/context` to
  inspect. Hard reset = exit the process.
- **CrewAI** `[crewai/memory]`: session state is *split* — the in-process Crew
  and an opt-in persistent store. `memory=False` (the default) is the debug
  posture; a `Crew()` re-instantiation clears the in-process state but **not** the
  persistent LanceDB store. `agent.reset()` / fresh `Agent()` clears per-agent
  state. Always `memory=False` while debugging.
- **LangGraph** `[langgraph/persistence]` `[langgraph/subgraphs]`: state is keyed
  by `thread_id` in a checkpointer. A new `thread_id` = a clean conversation;
  reusing one resumes from the checkpoint. `update_state(messages=...)` is the
  finest-grained partial clear in any surveyed tool. Subgraphs give *structural*
  isolation — a sub-task with its own state schema can't bleed into the parent
  except on shared keys, the architecture-level analogue of `/clear`.

### Picking across them
The SOP is identical everywhere: **detect bleed → save what's durable → cut at
the smallest correct size → restart focused.** Only the command changes. If you
work across tools, internalize the *move*, not the syntax — the table above maps
the move onto each tool's command.

---

## 附录 · 引用速查 (Citation Index)

Short tags used inline → full sources in `references/R1-source-evidence.md`.

- `[aider/commands]` = aider.chat/docs/usage/commands.html (`/clear`, `/reset`, `/drop`, `/tokens`)
- `[aider/edit-errors]` = aider.chat/docs/troubleshooting/edit-errors.html (~25k distraction threshold; `/clear` as first-line fix)
- `[aider/conventions]` = aider.chat/docs/usage/conventions.html (CONVENTIONS.md persistence)
- `[claude-code/slash]` = docs.anthropic.com/en/docs/claude-code/slash-commands (`/clear`, `/context`)
- `[crewai/memory]` = docs.crewai.com/en/concepts/memory (opt-in memory; debug with memory=False)
- `[langgraph/persistence]` = langchain-ai.github.io/langgraph/concepts/persistence/ (thread_id scopes state)
- `[langgraph/manage-history]` = langchain-ai.github.io/langgraph/how-tos/manage-conversation-history/ (update_state, RemoveMessage)
- `[langgraph/subgraphs]` = langchain-ai.github.io/langgraph/concepts/subgraphs/ (isolated child state)
- `[langgraph/hitl]` = docs.bswen.com/blog/2026-04-16-langgraph-human-in-the-loop/ (TTL sweep for abandoned threads)

Local sibling SOPs this skill distills from:
- `aider-sop-skill/SKILL.md` — §6 context-hygiene table; §5 Case 3 (`/clear` as debugging move)
- `crewai-sop-skill/SKILL.md` — DC-4 (memory default off), OP-5 (memory guidance)
- `langgraph-sop-skill/SKILL.md` — OP-6 (subgraph isolation), OP-10 (time-travel from checkpoint), §2 (thread_id as session identity)
