---
name: running-claude-code-via-litellm-copilot
description: Use when routing Claude Code through a local LiteLLM proxy to GitHub Copilot, reducing direct Anthropic spend, configuring ANTHROPIC_BASE_URL or ANTHROPIC_MODEL overrides, or troubleshooting Copilot proxy setup failures such as model-not-found, no localhost traffic, or GitHub 401/403 auth errors.
---

## Overview

Use this skill for the specific workaround where Claude Code keeps its Anthropic-shaped client behavior, but the actual backend traffic is sent to a local LiteLLM proxy and then forwarded to GitHub Copilot.

Treat this as an advanced workaround, not an officially guaranteed GitHub workflow. Help the user succeed technically, but do not promise GitHub support, policy approval, or long-term compatibility.

This skill is guidance-first but execution-aware:

- If the user wants explanation only, provide the smallest correct set of files, commands, and checks.
- If the user wants real setup work on the current machine, inspect first and adapt commands to the active shell and OS.
- Pause before persistent edits such as `~/.claude/settings.json` or shell profile files.

Read [`references/doc-verified-notes.md`](./references/doc-verified-notes.md) before answering if you need to justify which parts come from the article and which parts were tightened against current LiteLLM docs.

## When To Use

Use this skill when the user wants any of the following:

- Claude Code to run against GitHub Copilot through LiteLLM
- lower direct Anthropic API spending while keeping the Claude Code workflow
- a local `config.yaml` for LiteLLM's GitHub Copilot provider
- `ANTHROPIC_BASE_URL`, `ANTHROPIC_MODEL`, or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` setup
- help understanding GitHub device authorization during LiteLLM startup
- help with model mismatch, 404-like errors, no requests reaching LiteLLM, or GitHub 401/403 failures

Do not use this skill for:

- deciding whether the workaround is allowed by GitHub terms
- general LiteLLM architecture unrelated to Claude Code plus Copilot
- direct Anthropic API setup with no Copilot or LiteLLM component

## Core Rules

1. Lead with a short compliance caveat.
   Explain that this is a workaround based on a local proxy path, not a GitHub-promoted workflow, and the user must evaluate the latest Copilot terms and limits for themselves.
2. Prefer the minimum viable path first.
   Start with temporary environment variables and a local `config.yaml` unless the user explicitly wants a persistent setup.
3. Keep `ANTHROPIC_MODEL` and LiteLLM `model_name` identical.
   Exact string match matters more than clever explanation.
4. Treat `ANTHROPIC_AUTH_TOKEN` as a local placeholder.
   Claude Code expects a non-empty value locally, but it is not the GitHub Copilot credential and should not be presented as a reusable secret.
5. Never overwrite `~/.claude/settings.json` wholesale.
   Merge only the needed `env` keys and preserve unrelated settings.

## Workflow

### 1. Preflight

Check these first when the user wants real setup work:

- `claude --help` succeeds
- `uv --version` or `pip --version` succeeds
- the user has GitHub Copilot access
- the intended LiteLLM port is available, usually `4000`

If the user only wants instructions, state the prerequisites instead of running them.

### 2. Choose Temporary vs Persistent Setup

Use this rule:

- Temporary setup: preferred default for first-time setup, debugging, and low-risk trials
- Persistent setup: only when the user explicitly wants the proxy path to apply every time Claude Code starts

For persistent setup, confirm the target file and then merge keys into `~/.claude/settings.json`. Do not replace the file contents.

### 3. Create LiteLLM `config.yaml`

Start from the article's flow, but keep the provider naming aligned with LiteLLM docs:

```yaml
model_list:
  - model_name: claude-opus-4.5
    litellm_params:
      model: github_copilot/claude-opus-4.5
      drop_params: true
```

Explain the fields:

- `model_name`: the logical name Claude Code will request
- `model`: the LiteLLM provider route, using `github_copilot/<model>`
- `drop_params: true`: strips unsupported Anthropic-specific fields before forwarding to Copilot

If the user wants a different Copilot-backed model, keep the same pattern:

```yaml
model_list:
  - model_name: <logical-name>
    litellm_params:
      model: github_copilot/<copilot-model>
      drop_params: true
```

Do not hardcode extra headers into the default path unless the user already hit a rejection that suggests header overrides are needed.

### 4. Install and Start LiteLLM

Preferred install:

```bash
uv tool install "litellm[proxy]"
```

Fallback:

```bash
pip install "litellm[proxy]"
```

Start the proxy from the directory containing `config.yaml`:

```bash
litellm --config config.yaml --port 4000
```

Tell the user to keep that terminal open because the logs are the fastest truth source during verification.

### 5. Explain GitHub Device Authorization

On the first successful request to the GitHub Copilot provider, LiteLLM may open a device authorization flow:

1. LiteLLM prints a verification URL and device code
2. the user opens the URL and approves the request
3. LiteLLM stores the resulting credential locally for future use

Optional token-location overrides exist:

- `GITHUB_COPILOT_TOKEN_DIR`
- `GITHUB_COPILOT_ACCESS_TOKEN_FILE`

Only mention these when the user needs custom token storage, shared environments, or troubleshooting around expired or misplaced credentials.

### 6. Configure Claude Code

For a temporary PowerShell session:

```powershell
$env:ANTHROPIC_AUTH_TOKEN = "sk-any-string"
$env:ANTHROPIC_BASE_URL = "http://localhost:4000"
$env:ANTHROPIC_MODEL = "claude-opus-4.5"
$env:CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC = "1"
claude
```

For a temporary Bash or Zsh session:

```bash
export ANTHROPIC_AUTH_TOKEN="sk-any-string"
export ANTHROPIC_BASE_URL="http://localhost:4000"
export ANTHROPIC_MODEL="claude-opus-4.5"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
claude
```

For persistent configuration, merge these keys into `~/.claude/settings.json`:

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "sk-any-string",
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_MODEL": "claude-opus-4.5",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"
  }
}
```

Merge-safe behavior:

- if the file does not exist, create it
- if it exists, preserve all unrelated top-level keys
- preserve existing `env` entries that are unrelated to this workflow
- update only the four keys above
- if the JSON is malformed, stop and report the parse problem instead of overwriting the file

### 7. Verify The Request Chain

Use two terminals when possible:

- Terminal A runs LiteLLM
- Terminal B runs `claude`

Ask for one small prompt such as a short script or code review request, then verify:

- Claude Code starts normally
- LiteLLM logs show an inbound request
- LiteLLM logs indicate the GitHub Copilot model route, typically `github_copilot/<model>`

The healthy path is:

```text
Claude Code -> LiteLLM -> GitHub Copilot -> LiteLLM -> Claude Code
```

### 8. Troubleshooting

If Claude Code reports model-not-found, 404-like failures, or LiteLLM says the model does not exist:

- compare `ANTHROPIC_MODEL` to `model_name` exactly
- check case, punctuation, and hyphens

If LiteLLM never receives a request:

- confirm `ANTHROPIC_BASE_URL` points to <http://localhost:4000>
- confirm LiteLLM is still running on that port
- confirm the environment variables were set in the same shell session that launched `claude`
- check local firewall or port conflicts if the URL is correct but still silent

If LiteLLM reaches GitHub Copilot but gets 401 or 403 responses:

- repeat the device authorization flow by restarting LiteLLM and retrying
- confirm the GitHub account still has Copilot access
- if custom token-directory variables are set, verify they point to the intended files

## Advanced Fallback: Header Overrides

The article uses explicit Copilot-style headers. Current LiteLLM docs expose GitHub Copilot as a provider and also document header override support.

Only reach for explicit `extra_headers` when:

- the basic provider flow reaches Copilot but still needs client-shape overrides
- the user already has evidence that a specific environment behaves better with editor-style headers

Example fallback:

```yaml
model_list:
  - model_name: claude-opus-4.5
    litellm_params:
      model: github_copilot/claude-opus-4.5
      drop_params: true
      extra_headers:
        editor-version: "vscode/1.85.1"
        editor-plugin-version: "copilot/1.155.0"
        Copilot-Integration-Id: "vscode-chat"
        user-agent: "GithubCopilot/1.155.0"
```

Present this as an advanced fallback, not the universal default.

## Output Checklist

When answering a real user request with this skill, include:

- the brief compliance caveat
- the exact `config.yaml` or the delta to apply
- shell-appropriate commands
- whether the setup is temporary or persistent
- the verification path
- the smallest relevant troubleshooting section if something failed

## Safety Reminders

- Do not state that GitHub officially supports this workaround.
- Do not imply that a dummy `ANTHROPIC_AUTH_TOKEN` is a real Copilot credential.
- Do not recommend replacing `~/.claude/settings.json` wholesale.
- Do not present stale model names as guaranteed current availability; if the user asks for a specific model, keep the `github_copilot/<model>` pattern and note that Copilot-exposed model availability may change.
