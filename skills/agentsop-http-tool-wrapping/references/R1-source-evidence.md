# R1 — Source Evidence

Citations and quoted evidence backing every claim in `SKILL.md`. Organized by topic.

---

## 1. Official framework tool/function-calling docs

### OpenAI function calling
- **Source**: `developers.openai.com/api/docs/guides/function-calling`
- **Key extract**: "Since model responses can include zero, one, or multiple calls, it is best practice to assume there are several." → motivates parallel-call safe wrappers (OP-5, OP-9).
- **Source**: `developers.openai.com/api/docs/guides/tools`
- **Key extract**: "Take advantage of the `allowed_tools` parameter to use only the tools that are necessary and save on unnecessary context." → motivates per-step tool scoping (cross-link to per-agent tool scoping from CrewAI).
- **Source**: `community.openai.com/t/prompting-best-practices-for-tool-use-function-calling/1123036`
- **Key extract**: Tool name should be a verb; description should explain *when* to call, not *how*.

### Anthropic tool_use
- **Source**: `docs.anthropic.com/en/api/overview` and `docs.anthropic.com/en/docs/build-with-claude/tool-use`
- **Key extract**: "Client side tools require you to call them on behalf of the LLM and then provide back in a `tool_result` with a matching `tool_use_id` to identify the original tool use request." → motivates the request/response correlation contract.
- **Schema**: Tools defined with `{name, description, input_schema}` (JSON Schema). Mirrors OpenAI's shape closely enough that one Pydantic model serves both (OP-10).

### LangChain `@tool` / StructuredTool
- **Source**: `docs.langchain.com/oss/python/langchain/tools`
- **Key extract**: "Type hints are required as they define the tool's input schema, and the docstring should be informative and concise to help the model understand the tool's purpose."
- **Source**: `python.langchain.com/api_reference/core/tools/langchain_core.tools.simple.Tool.html`
- **Key extract**: "Defining the `args_schema` is recommended as it allows adding field details and helps with validation and integrations."
- **Source**: `changelog.langchain.com/announcements/improved-pydantic-2-support-with-langchain-tool-apis`
- **Key extract**: Pydantic v2 first-class for `BaseTool` / `StructuredTool` since mid-2025.
- **Source**: `blog.langchain.com/structured-tools/`
- **Key extract**: Errors raised inside a tool can be converted by `ToolException` into LM-visible strings.

### CrewAI tools (per-agent scoping)
- **Source**: `docs.crewai.com/en/concepts/tools`
- **Key extract**: "write once, use everywhere — tool definitions are reusable; but each agent only gets the tools its role requires."
- **Source**: `community.crewai.com/t/tool-best-practice-assign-to-agent-or-task/5919`
- **Key extract**: Community consensus: shared tool *definition*, per-agent *binding*. Carried into OP-10 (framework-binding) and noted in §7 cross-framework table.

### LangGraph tool node
- **Source**: `langchain-ai.github.io/langgraph/how-tos/tool-calling/`
- **Key extract**: `ToolNode` wraps a list of tools; conditional edge routes on `tool_calls`. Tools are plain `@tool`-decorated functions — wrapping rules are identical to LangChain.

### MCP HTTP server
- **Source**: `modelcontextprotocol.io` and `gun.io/ai/2025/05/wrap-existing-api-with-mcp/`
- **Key extract**: "REST endpoints that retrieve data (GET) typically map to MCP resources. Endpoints that create, update, or delete data (POST, PUT, DELETE) work better as MCP tools." → informs DC-1 (resource vs tool split).
- **Source**: `northflank.com/blog/how-to-build-and-deploy-a-model-context-protocol-mcp-server`
- **Key extract**: "Store your REST API authentication tokens (like API keys or OAuth tokens) in environment variables or secure storage. Then, include these tokens in the HTTP requests your MCP handlers make to the underlying REST endpoints." → OP-4 evidence.
- **Source**: `stainless.com/mcp/from-rest-api-to-mcp-server/`
- **Key extract**: Auto-generated 1:1 MCP servers from OpenAPI specs are a starting point but routinely under-perform hand-curated tools — direct evidence for **AP-1** (1:1 endpoint mapping).

---

## 2. HTTP reliability — retries, rate limits, pagination, idempotency

### Rate limits
- **Source**: `apxml.com/courses/building-advanced-llm-agent-tools/chapter-4-integrating-external-apis-tools/api-rate-limits-retries-tools`
- **Key extract**: "Catch 429 responses, read the `Retry-After` header for the exact wait time, implement exponential backoff with jitter if no header is present, and queue non-urgent requests rather than retrying immediately." → OP-5.
- **Source**: `getknit.dev/blog/10-best-practices-for-api-rate-limiting-and-throttling` (2026 update)
- **Key extract**: Standard 429 response shape; client should respect `X-RateLimit-Reset` and `Retry-After`.

### Retry with jitter
- **Source**: `boldsign.com/blogs/api-retry-mechanism-how-it-works-best-practices/`
- **Key extract**: "Without jitter, many clients fail at the same time, compute the same backoff, and retry in sync, creating a thundering herd." → OP-5 requires jitter.
- **Standard stack**: AWS architecture blog "Exponential Backoff and Jitter" (canonical reference, cited universally).

### Idempotency
- **Source**: `techopsasia.com/blog/rest-api-design-idempotency-pagination-security`
- **Key extract**: "Every mutating endpoint should support idempotency keys — a client-generated identifier that ensures the same logical operation produces the same result regardless of how many times it's submitted." → OP-9.
- **Source**: `mightybot.ai/blog/fault-tolerant-ai-agent-pipelines/`
- **Key extract**: Agent retries amplify dup-write risk because the LM cannot easily distinguish "did my call succeed?" from "is the response missing?".
- **Stripe API docs** (canonical industry example): `stripe.com/docs/api/idempotent_requests` — `Idempotency-Key` header pattern.

### Pagination
- **Source**: `techopsasia.com/blog/rest-api-design-idempotency-pagination-security`
- **Key extract**: "Cursor-based pagination provides better performance and consistency, where cursors encode position information ... and remain stable even when new items are added. Cursor-based pagination is more reliable than offset/limit for agentic scrolling." → OP-6.
- **Source**: `zuplo.com/learning-center/api-readiness-gap-agent-callable-apis`
- **Key extract**: "AI agents generate traffic patterns that look nothing like human usage. A single agent might burst 20 sequential API calls to complete one task." → motivates bounded auto-loop (cross-link to T2 bounded-loop skill).

---

## 3. Tool schema design & description

- **Source**: `medium.com/@1nick1patel1/tool-schemas-the-quiet-superpower-of-agents`
- **Key extract**: "A mega-tool with a single instructions string invites hallucinations." → DC-1 evidence.
- **Source**: `apxml.com/courses/building-advanced-llm-agent-tools/chapter-1-llm-agent-tooling-foundations/tool-input-output-schemas`
- **Key extract**: "If a field represents a date, specify if it's a date string (and ideally, the format, e.g., ISO 8601) or a Unix timestamp." → OP-3 (per-field `description=`).
- **Key extract**: "Tool descriptions are often more important than code comments because the LLM directly uses them for reasoning." — quoted in `SKILL.md` §2.
- **Source**: `arxiv.org/pdf/2403.00839` (ToolNet, Liu et al. 2024)
- **Key extract**: At >50 tools, flat tool-list catalogs degrade selection accuracy; hierarchical / graph organization helps. → DC-1 fallback strategy.

---

## 4. Agent-ready API design (external view)

- **Source**: `sergheipogor.medium.com/how-to-make-your-api-agent-ready-design-principles-for-the-agentic-era-75f3c086ca70`
- **Key extract**: Surface intent, not CRUD verbs; return machine-readable error codes; document semantic constraints in the schema, not in prose docs.
- **Source**: `zuplo.com/learning-center/api-readiness-gap-agent-callable-apis`
- **Key extract**: "Return machine-readable rate limit headers that agents can use to self-throttle." — used verbatim in §2 mental model.

---

## 5. Cross-framework comparison sources

- LangChain tools docs: `docs.langchain.com/oss/python/langchain/tools`
- LangGraph prebuilt: `langchain-ai.github.io/langgraph/agents/agents/`
- CrewAI tools: `docs.crewai.com/en/concepts/tools`
- OpenAI function calling: `developers.openai.com/api/docs/guides/function-calling`
- Anthropic tool use: `docs.anthropic.com/en/docs/build-with-claude/tool-use`
- MCP spec: `modelcontextprotocol.io/specification`
- FastMCP (Python SDK): `github.com/jlowin/fastmcp`

All five paths can consume the same Pydantic v2 model via `Model.model_json_schema()` and `Model.model_validate(json_input)` — the wrapper logic (auth, retry, pagination, shaping) is framework-independent. The framework-specific layer is just the *registration* call (OP-10).
