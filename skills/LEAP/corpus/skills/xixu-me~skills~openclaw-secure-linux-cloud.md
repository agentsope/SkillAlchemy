---
name: openclaw-secure-linux-cloud
description: Use when self-hosting OpenClaw on a cloud server, hardening a remote OpenClaw gateway, choosing between SSH tunneling, Tailscale, or reverse-proxy exposure, or reviewing Podman, pairing, sandboxing, token auth, and tool-permission defaults for a secure personal deployment.
---

## Overview

Use this skill for the conservative "deploy first, expose later" pattern for
OpenClaw on a cloud server.

Default to a private control plane:

- Harden the Linux host before exposing anything.
- Keep the gateway bound to `127.0.0.1`.
- Reach the Control UI through an SSH tunnel first.
- Keep token authentication, pairing, and sandboxing enabled.
- Start with a narrow tool profile and loosen only with an explicit need.

This skill is for secure Linux cloud hosting. If the user only wants the
fastest generic OpenClaw install on a local machine, prefer the official
OpenClaw onboarding docs instead of forcing this flow.

Open [`references/REFERENCE.md`](./references/REFERENCE.md) when you need the
command matrix, baseline config shape, checklist, or access-path comparison.

## When To Use

Use this skill when the user mentions any of the following:

- OpenClaw on a cloud server, VM, or other Linux host
- Secure self-hosting, hardening, or "run it privately"
- Podman, loopback binding, SSH tunneling, or remote Control UI access
- Tailscale vs reverse proxy for OpenClaw
- Pairing, sandboxing, token auth, or locked-down tool permissions
- Reviewing whether an existing OpenClaw host is too exposed

Do not use this skill for:

- General Linux hardening with no OpenClaw component
- Local single-machine onboarding where remote access is irrelevant
- Pure local onboarding with no remote-host hardening questions
- Non-Linux hosting unless the user explicitly wants this Linux-first pattern
  adapted

## Workflow

### 1. Classify the request

Put the task in one of these buckets before giving detailed guidance:

1. **Fresh deploy**: the user wants to stand up OpenClaw securely on a Linux
   cloud host from scratch.
2. **Hardening review**: the user already has OpenClaw running and wants to
   reduce exposure or audit risky defaults.
3. **Access-model decision**: the user is choosing between SSH tunneling,
   Tailscale, or a reverse proxy.

### 2. Start from the secure baseline

Unless the user clearly asks for something else, recommend this baseline:

- Harden the Linux host first: updates, SSH keys, SSH lock-down, and a
  default-deny inbound firewall matched to the distro.
- Run OpenClaw under rootless Podman rather than as a root-owned long-lived
  process.
- Keep the gateway on loopback only.
- Keep the Control UI private and access it through an SSH tunnel.
- Require token authentication.
- Keep pairing enabled for inbound messaging channels.
- Start with a minimal tool set and sandbox sessions by default.

Treat these as explicit red flags:

- Binding the gateway to `0.0.0.0`
- Opening port `18789` to the public internet
- Turning on broad runtime, filesystem, automation, or browser access by
  default
- Leaving `~/.openclaw` readable by other local users

### 3. Separate local and server actions

Always distinguish between:

- **Local machine actions**: SSH key generation, tunnel setup, browser access
- **Server actions**: Linux hardening, Podman install path, OpenClaw service
  setup, config permissions, service restarts

Do not blur the two execution contexts together. The user should be able to
tell which commands run on their laptop and which run on the Linux host.

### 4. Ask only for blocking facts

Only stop for missing facts that change the safe path, such as:

- Linux distro and host access details when package-manager or firewall
  commands matter
- Whether OpenClaw is already installed
- Whether the user truly needs repeated remote private access or public access
- Whether an existing deployment is already reachable from the internet

If a detail is not safety-critical, make the reasonable secure assumption and
state it.

### 5. Use the access escalation ladder

Recommend remote access in this order:

1. **SSH tunnel**: default for first deployment and personal use
2. **Tailscale**: next step when the user needs repeated private access across
   trusted devices
3. **Reverse proxy**: only when the user explicitly needs public exposure and
   accepts the extra hardening burden

If the user asks for Tailscale or reverse proxy, still explain why the loopback
binding and private-first model remain the baseline.

## Output Expectations

For a fresh deployment, provide:

- A short architecture summary
- Local-vs-server steps
- A conservative config baseline
- A pre-launch checklist
- A short "what not to expose" warning

For a hardening review, provide:

- The likely risks in the current setup
- A prioritized remediation sequence
- Any immediate exposure concerns to fix before anything else

For an access-path decision, provide:

- A recommendation
- Why it is the lowest-risk fit
- What extra safeguards are required if the user chooses a broader exposure
  model

## Common Mistakes

- Treating OpenClaw like a normal public web app on day one
- Assuming auth alone replaces network boundaries
- Turning on more tool power before the user has a clear workflow that needs it
- Disabling pairing just to save time during early setup
- Skipping follow-up audits after changing config or sandbox settings

## Reference Usage

Use [`references/REFERENCE.md`](./references/REFERENCE.md) when you need:

- The cross-distro hardening flow and Debian/Ubuntu example commands
- The Podman-based OpenClaw setup outline
- The baseline config skeleton
- The pre-launch checklist
- The day-to-day audit commands
- The SSH tunnel vs Tailscale vs reverse-proxy comparison
