# R2 — Tool Commands Cheat Sheet

Concrete commands for clearing / managing session state in every framework this skill covers. Copy-pastable.

---

## Aider

```text
/tokens               # inspect current context size — first move
/drop <file>          # remove a file from the working set (no chat clear)
/drop                 # drop all files
/clear                # wipe chat history; keep /add'd files
/reset                # wipe chat history AND drop all files
/ls                   # list files currently in scope
/map                  # show repo-map (audit context size)
```

**When to use which**:
- `> 25k tokens` and growing → `/tokens` then `/drop` unused files first; if still high, `/clear`.
- Topic switch on the same codebase → `/clear` (keep files).
- Brand-new task → `/reset` (or just exit and re-launch).
- Repeated "SEARCH block not found" → `/clear` BEFORE swapping model/edit-format.

**CLI flags relevant to state**:
```bash
aider --map-tokens 1024      # cap repo-map size
aider --subtree-only         # restrict scope to current subdir
aider --no-git               # no auto-commits (loses safety net; not recommended)
```

Source: `aider.chat/docs/usage/commands.html`, `aider.chat/docs/troubleshooting/edit-errors.html`

---

## Claude Code

```text
/clear                # reset conversation history (preserves files on disk)
/context              # inspect what's currently in context
```

**When to use**:
- Topic switch in the same terminal → `/clear`.
- Hard reset (lose env, settings) → exit the CLI process and re-launch.
- Files on disk are NEVER touched by `/clear`.

**Pre-`/clear` ritual**:
```text
> summarize the decisions we've made, the files we've edited, and the open questions in one paragraph
[copy the paragraph]
> /clear
> [paste the paragraph back as the first message]
```

Source: `docs.anthropic.com/en/docs/claude-code/slash-commands`

---

## CrewAI

```python
# Debug: turn memory off (default is already off, but be explicit)
crew = Crew(
    agents=[...],
    tasks=[...],
    memory=False,           # ← off during debug
    verbose=True,
)

# Re-instantiate between debug runs — do NOT reuse the Crew object
def fresh_crew():
    return Crew(agents=fresh_agents(), tasks=fresh_tasks(), memory=False)

# If memory=True was in use, wipe the store before next run
# Default backend is LanceDB under ~/.crewai/
# rm -rf ~/.crewai/storage/

# Reset a single agent's in-process state
agent = Agent(role="...", goal="...", backstory="...")  # new instance
```

**When to use which**:
- Debug session → `memory=False` always.
- Cross-kickoff persistence needed in prod → `memory=True` with Mem0 backend, NOT default LanceDB.
- "Agent still remembers a thing I cleared" → wipe the persistent store explicitly; the in-memory `Crew()` re-instantiation alone won't clear it.

Source: `docs.crewai.com/en/concepts/memory`, `crewai-sop-skill/SKILL.md` DC-4.

---

## LangGraph

```python
from uuid import uuid4
from langgraph.graph import StateGraph, END
from langchain_core.messages import RemoveMessage

# (a) Fresh thread — clean slate, same compiled graph
new_thread_config = {"configurable": {"thread_id": str(uuid4())}}
graph.invoke(initial_input, config=new_thread_config)

# (b) Surgical state edit — keep thread, trim messages
current = graph.get_state(config)
trimmed = current.values["messages"][-5:]          # keep last 5 only
graph.update_state(config, {"messages": trimmed})

# (b') Or delete specific messages by id
graph.update_state(
    config,
    {"messages": [RemoveMessage(id=m.id) for m in messages_to_drop]},
)

# (c) Subgraph isolation — child has own state schema
class ChildState(TypedDict):
    docs: list[str]                       # only this key crosses

class ParentState(TypedDict):
    docs: list[str]
    other_parent_only_field: str

child_graph = StateGraph(ChildState)...compile()
parent.add_node("research", child_graph)  # bleed limited to shared keys
```

**When to use which**:
- "Start over with this user" → new `thread_id` (a).
- "History is mostly fine, one bad turn" → `update_state` with trimmed messages (b/b').
- "This sub-workflow should not see parent's chat" → subgraph (c) — architectural fix, not runtime.

Source: `langchain-ai.github.io/langgraph/concepts/persistence/`, `.../how-tos/manage-conversation-history/`, `.../concepts/subgraphs/`.

---

## ChatGPT / Gemini / Claude.ai web

```text
[ "New chat" button ]                     # only reliable primitive
```

**Pre-clear ritual** (same as Claude Code):
```text
You: summarize what we decided and the current state in one paragraph
[copy]
[ click New chat ]
You: [paste paragraph]; continue from here.
```

**Caveat — persistent memory features**:
- ChatGPT has cross-chat memory; "New chat" does NOT wipe it. Go to Settings → Personalization → Memory → Manage to clear specific memories.
- Same warning applies to any web UI advertising "remembers you across sessions" — clearing a chat ≠ clearing the memory store.

---

## Raw OpenAI / Anthropic SDK

There is no "session" — you control the message list directly. The discipline is:

```python
# Bad: append forever
messages.append({"role": "user", "content": new_input})

# Good: bound the history
MAX_MSGS = 20
messages = messages[-MAX_MSGS:]

# Better: summarize + truncate when over budget
if total_tokens(messages) > 25_000:
    summary = summarize(messages[:-4])
    messages = [{"role": "system", "content": f"Earlier context: {summary}"}] + messages[-4:]
```

This is the *same SOP*: detect bloat, summarize, restart with distilled state.

---

## One-page cross-framework quick reference

| Need | Aider | Claude Code | CrewAI | LangGraph | ChatGPT/web |
|---|---|---|---|---|---|
| Inspect context size | `/tokens` | `/context` | (LangSmith / logs) | `len(state['messages'])` | (UI hint) |
| Clear chat, keep files | `/clear` | `/clear` | re-instantiate Crew | new `thread_id` | New chat |
| Hard reset everything | `/reset` | exit CLI | new process | new `thread_id` | New chat (+ clear memory in Settings) |
| Partial clear (drop subset) | `/drop <files>` | n/a | re-instantiate Agent | `update_state({'messages':...})` | n/a |
| Isolate sub-task | new aider window | (sub-process) | separate Crew | subgraph w/ own schema | New chat |

**Universal pre-clear ritual**: summarize → copy → clear → paste summary. Works in every cell of the table above.
