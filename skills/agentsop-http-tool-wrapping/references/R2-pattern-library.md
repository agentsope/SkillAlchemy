# R2 — Pattern Library

Reusable, framework-independent code shapes referenced by `SKILL.md`. These are
the *what good looks like* templates for each operation. Python + Pydantic v2 +
httpx; the same models bind into every framework (see §7 of `SKILL.md`).

---

## P1 · Typed input schema (OP-3)

The schema is the prompt. Every field carries a model-facing `description=`.
Flatten the wire format — the model never builds query strings.

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

class SearchOrdersInput(BaseModel):
    """Search a customer's orders by status and date. Use to find orders
    before acting on one (e.g. before cancel_order)."""
    customer_email: str = Field(..., description="Customer email, exact match.")
    status: Literal["open", "shipped", "cancelled"] = Field(
        "open", description="Order status filter. Defaults to open orders.")
    since: Optional[str] = Field(
        None, description="ISO 8601 date (YYYY-MM-DD). Only orders on/after this date.")
    limit: int = Field(20, ge=1, le=100, description="Max orders to return (1-100).")
```

Anti-pattern this replaces (AP-7): `def search(params: dict)` or `body: str`.

---

## P2 · Output shaping model (OP-7, DC-2)

Return only what the agent needs to reason or act. Demote bulk to a cursor.

```python
class OrderSummary(BaseModel):
    order_id: str
    status: str
    total_usd: float
    placed_on: str               # ISO date, not raw timestamp
    item_count: int              # not the full item array

class SearchOrdersOutput(BaseModel):
    orders: list[OrderSummary]   # thin slice, NOT the raw 10MB doc
    next_cursor: Optional[str] = None   # agent calls again only if needed
```

---

## P3 · Resilient HTTP client: timeout + jittered retry (OP-5)

Retry only on 429/5xx/network. Honor `Retry-After`. Jitter prevents thundering
herd `[boldsign/retry]`. Never retry other 4xx.

```python
import httpx, random, time

RETRYABLE = {429, 500, 502, 503, 504}

def request_with_retry(client: httpx.Client, method: str, url: str,
                       *, max_attempts: int = 4, base: float = 0.5, **kw) -> httpx.Response:
    for attempt in range(max_attempts):
        try:
            resp = client.request(method, url, timeout=10.0, **kw)  # per-attempt timeout
        except (httpx.TimeoutException, httpx.TransportError):
            if attempt == max_attempts - 1:
                raise
            time.sleep(base * (2 ** attempt) + random.uniform(0, base))
            continue
        if resp.status_code in RETRYABLE and attempt < max_attempts - 1:
            wait = float(resp.headers.get("Retry-After", base * (2 ** attempt)))
            time.sleep(wait + random.uniform(0, base))   # jitter
            continue
        return resp
    return resp
```

---

## P4 · Error → LM-readable contract (OP-8)

Closed code set. Never leak a stack trace to the model `[lc/structured]`.

```python
class ToolError(BaseModel):
    error: Literal["not_found", "invalid_input", "auth_failed",
                   "rate_limited", "server_error"]
    message: str
    retryable: bool
    hint: str = ""

def to_tool_error(resp: httpx.Response) -> ToolError:
    code = resp.status_code
    if code == 404: return ToolError(error="not_found", message=resp.text[:200], retryable=False)
    if code in (401, 403): return ToolError(error="auth_failed", message="check credentials", retryable=False)
    if code == 422: return ToolError(error="invalid_input", message=resp.text[:200], retryable=False,
                                     hint="fix the arguments and call again")
    if code == 429: return ToolError(error="rate_limited", message="slow down", retryable=True,
                                     hint=f"retry after {resp.headers.get('Retry-After','a few')}s")
    return ToolError(error="server_error", message=resp.text[:200], retryable=True)
```

---

## P5 · Auth injection at the boundary (OP-4)

Secret read inside the wrapper. Never a tool param, never in the description.
Per-tenant token via closure/context, not args `[northflank/mcp]`.

```python
import os

def make_client(tenant_token: str | None = None) -> httpx.Client:
    token = tenant_token or os.environ["ORDERS_API_KEY"]   # env / secret store
    return httpx.Client(base_url="https://api.example.com",
                        headers={"Authorization": f"Bearer {token}"})
```

The model's schema (`SearchOrdersInput`) has *no* `api_key` field.

---

## P6 · Pagination — one page + cursor (OP-6, DC-2)

Default: return one page, let the agent decide. Cursor over offset
`[techops/rest]`. Bounded auto-loop only for small totals.

```python
def search_orders_page(inp: SearchOrdersInput, cursor: str | None,
                       client: httpx.Client) -> SearchOrdersOutput:
    params = {"email": inp.customer_email, "status": inp.status, "limit": inp.limit}
    if inp.since: params["since"] = inp.since
    if cursor: params["cursor"] = cursor
    resp = request_with_retry(client, "GET", "/orders", params=params)
    if resp.status_code != 200:
        return to_tool_error(resp)            # P4
    body = resp.json()
    return SearchOrdersOutput(
        orders=[OrderSummary(**o) for o in body["data"]],
        next_cursor=body.get("next_cursor"),  # agent calls again only if set
    )
```

---

## P7 · Idempotency hook on mutations (OP-9)

Flag only — full protocol lives in the `llm-tool-idempotency` skill.

```python
import uuid

def cancel_order(order_id: str, client: httpx.Client) -> dict:
    key = str(uuid.uuid4())   # or derive deterministically from logical op
    resp = request_with_retry(client, "POST", f"/orders/{order_id}/cancel",
                              headers={"Idempotency-Key": key})   # Stripe pattern
    return resp.json() if resp.status_code == 200 else to_tool_error(resp).model_dump()

cancel_order.metadata = {"mutating": True, "idempotent": True}
```

---

## P8 · Framework binding — one schema, five targets (OP-10, §7)

```python
# LangChain / LangGraph
from langchain_core.tools import tool

@tool(args_schema=SearchOrdersInput)
def search_orders(customer_email: str, status: str = "open",
                  since: str | None = None, limit: int = 20) -> dict:
    """Search a customer's orders. See SearchOrdersInput for fields."""
    with make_client() as c:
        return search_orders_page(SearchOrdersInput(customer_email=customer_email,
            status=status, since=since, limit=limit), None, c).model_dump()

# CrewAI
from crewai.tools import BaseTool
class SearchOrdersTool(BaseTool):
    name: str = "search_orders"
    description: str = "Search a customer's orders by status and date."
    args_schema: type[BaseModel] = SearchOrdersInput
    def _run(self, **kw) -> dict:
        with make_client() as c:
            return search_orders_page(SearchOrdersInput(**kw), None, c).model_dump()

# OpenAI function calling — schema straight from Pydantic
openai_tool = {"type": "function", "function": {
    "name": "search_orders",
    "description": "Search a customer's orders by status and date.",
    "parameters": SearchOrdersInput.model_json_schema()}}

# Anthropic tool_use
anthropic_tool = {"name": "search_orders",
    "description": "Search a customer's orders by status and date.",
    "input_schema": SearchOrdersInput.model_json_schema()}

# MCP (FastMCP) — schema inferred from type hints
# from mcp.server.fastmcp import FastMCP
# mcp = FastMCP("orders")
# @mcp.tool()
# def search_orders(customer_email: str, status: str = "open", ...) -> dict: ...
```

The robustness layer (P3–P7) is shared; only the registration call differs.

---

## P9 · Wide-API typed grouping (DC-1)

Between 1:1 (too many tools) and one mega-blob (no validation): group by
sub-domain with a *typed* action enum, never a free-form string.

```python
class OrderAction(BaseModel):
    """Perform an order operation. Choose the action; provide its fields."""
    action: Literal["search", "get_status", "cancel"]   # typed, validatable
    order_id: Optional[str] = Field(None, description="Required for get_status/cancel.")
    customer_email: Optional[str] = Field(None, description="Required for search.")
    # validate per-action with a model_validator
```

Keeps the catalog short *and* keeps schema validation — the middle path in DC-1.
