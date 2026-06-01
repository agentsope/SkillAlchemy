---
name: secure-linux-web-hosting
description: Use when setting up, hardening, or reviewing a cloud server for self-hosting, including DNS, SSH, firewalls, Nginx, static-site hosting, reverse-proxying an app, HTTPS with Let's Encrypt or ACME clients, safe HTTP-to-HTTPS redirects, or optional post-launch network tuning such as BBR.
---

## Overview

Use this skill to turn a cloud server into a safely reachable web host
without leaning on stale distro-specific memory or outdated Debian-10-era
tutorials.

This skill keeps the familiar teaching arc of a beginner-friendly server guide,
but turns it into a reusable operator workflow:

1. Intake and routing
2. Prerequisites
3. Secure access
4. Firewall and exposure
5. Web server setup
6. Static site or app proxy
7. HTTPS
8. Validation
9. Optional advanced tuning

Before giving actionable commands, identify the distro family and verify the
current package names, service units, config paths, and ACME-client guidance
against official documentation for the user's distro and chosen tools.

Open [`references/workflow-map.md`](./references/workflow-map.md) first for the
phase sequence, then open the narrower reference file you need.

## When to Use

Use this skill when the user mentions any of the following:

- a cloud server, VM, droplet, or other Linux host they want to use for hosting
- connecting a domain or DNS A/AAAA record to a server
- SSH login, SSH hardening, root login, keys, ports, or firewall setup
- installing or configuring Nginx for a website
- serving a simple static site from Linux
- putting a small app behind Nginx as a reverse proxy
- HTTPS, Let's Encrypt, Certbot, `acme.sh`, certificate renewal, or redirecting
  HTTP to HTTPS
- optional post-setup performance or network tuning such as BBR

Do not use this skill for:

- Kubernetes, PaaS, or full container-orchestrator deployment design
- application-specific build or CI/CD questions where Linux hosting is not the
  actual problem
- Windows or macOS host administration
- public multi-tenant production architecture reviews that need a broader SRE
  or platform-design treatment

## Workflow

### 1. Intake and classify the current state

Start by identifying:

- distro family or image name
- whether the user has root access, an admin user, or only one live SSH session
- whether DNS already points at the host
- whether the goal is a static site or an app reverse proxy
- whether ports are already exposed
- whether HTTPS is already partially configured

If the distro is unknown, ask for it or have the user inspect `/etc/os-release`
before giving concrete package or service commands.

### 2. Verify current docs before actionable commands

Use bundled references for routing, then verify details against live official
docs before giving commands that depend on current distro behavior.

Always verify:

- package manager commands and package names
- firewall tooling and service names
- SSH service unit names and config include paths
- Nginx package and config layout
- the chosen ACME client's current instructions

If you cannot verify a detail, say so and give high-level guidance instead of
pretending the old Debian tutorial path is universal.

### 3. Keep the phases in order

Walk through the phases in this order unless the user is explicitly asking for
review or remediation of an existing setup:

1. prerequisites
2. secure access
3. firewall and exposure
4. web server
5. choose one hosting branch: static site or app proxy
6. HTTPS
7. validation
8. optional advanced tuning

Do not collapse the static-site branch and reverse-proxy branch into one
default answer. Pick the branch that matches the user's goal.

### 4. Enforce the safety gates

Treat these as hard stop checks:

- Do not recommend changing SSH port, disabling password auth, or disabling
  root SSH login until key-based login works in a second SSH session.
- Do not recommend certificate issuance until DNS resolves to the intended host
  and the HTTP site or proxy path works as expected.
- Do not force an HTTP-to-HTTPS redirect until HTTPS loads cleanly.
- Do not suggest BBR or similar tuning until secure hosting is already working.

Always distinguish:

- local-machine actions: SSH, DNS checks, browser tests
- server actions: package install, config edits, service reloads, firewall rules

## Output Expectations

For a fresh setup, provide:

- a brief diagnosis of the current state
- the current phase and why it comes next
- local-machine steps separate from server steps
- concrete commands or config snippets only after doc verification
- a verification step after each risky change
- a short "if this fails, check X" branch for the likely mistake at that phase

For a hardening or troubleshooting review, provide:

- the most likely risk or breakage first
- a prioritized remediation sequence
- the first safe verification step before the next config change

## Common Mistakes

- treating Debian-specific commands from an old article as Linux-universal
- hardening SSH in the only active session and locking the user out
- opening application ports directly instead of keeping the app on loopback
- mixing static-file hosting guidance and reverse-proxy guidance in one config
- attempting ACME issuance before DNS or HTTP is actually correct
- forcing redirects before HTTPS is proven
- treating BBR as part of the core setup instead of an optional later step
- ignoring SELinux or AppArmor differences when Nginx can read files on one
  distro but not another

## Reference Usage

Use [`references/workflow-map.md`](./references/workflow-map.md) for the phase map,
branching logic, and validation order.

Use [`references/distro-routing.md`](./references/distro-routing.md) when distro
family, package manager, firewall tooling, or config layout matters.

Use [`references/nginx-patterns.md`](./references/nginx-patterns.md) when the user
needs the static-site branch or the reverse-proxy branch.

Use [`references/security-and-tls.md`](./references/security-and-tls.md) for SSH
hardening sequence, firewall posture, certificate issuance, renewal, and
redirect timing.
