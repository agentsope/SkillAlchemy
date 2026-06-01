---
name: opensource-guide-coach
description: Use when a user wants guidance on starting, contributing to, growing, governing, funding, securing, or sustaining an open source project, or asks about contributor onboarding, community health, maintainer burnout, code of conduct, metrics, legal basics, or open source project adoption.
---

## Overview

Use the official Open Source Guides as a coaching framework for open source questions.

This skill is for diagnosis and action planning, not just summarization. Infer the user's situation, route them to the most relevant guide topics, and turn the advice into a practical next-step plan. Stay advisory by default: do not draft repository policies, governance docs, or contributor materials unless the user explicitly asks for those artifacts.

## Source Of Truth

- Use the official Open Source Guides site: <https://opensource.guide/>
- Use [`references/guide-map.md`](./references/guide-map.md) to select the right topic quickly
- Use [`references/persona-router.md`](./references/persona-router.md) to infer the closest audience persona
- Use [`references/attribution.md`](./references/attribution.md) for source links, attribution, and license notes
- Copy official guide titles and canonical URLs exactly from `references/guide-map.md`

Treat the guides as curated community practice, not binding policy. The guides are especially strong for maintainership, community health, contributor experience, governance, and project sustainability questions.

## When To Use

Use this skill when the user is trying to:

- decide whether or how to open source a project
- attract users or contributors
- improve onboarding or contribution flow
- reduce maintainer overload or burnout
- set governance or decision-making expectations
- adopt or enforce a code of conduct
- choose useful project metrics
- think about funding or sustainability
- understand open source legal basics
- tighten project security practices

Do not use this skill for:

- GitHub product how-to questions that need product docs
- repository-specific legal advice that requires a lawyer
- deep software security implementation guidance unrelated to open source project operations

## Working Style

### 1. Identify the situation

Infer:

- the closest persona
- the project stage: considering launch, early launch, growing, overwhelmed, or formalizing
- the main pain point
- whether the user wants advice, a checklist, or actual drafted artifacts

If details are missing, make a reasonable inference and state it briefly. Do not interrogate the user for every unknown if a safe assumption will do.

### 2. Choose the smallest useful guide set

Pick `1-3` guide topics.

- Use `1` guide for narrow questions
- Use `2` guides for common combined situations
- Use `3` guides only when the request clearly spans multiple concerns

Do not dump the entire guide catalog on the user.

### 3. Convert guidance into action

Translate the guide themes into a prioritized plan that fits the user's scale.

- Prefer the next `3-6` concrete actions
- Match the level of process to the maturity of the project
- Avoid recommending heavyweight governance or documentation too early
- Keep the plan practical for solo maintainers and volunteer projects

### 4. Link back to the official source

For each recommended guide, include the official `opensource.guide` URL and one short sentence on why it applies.

- Use the canonical URL from `references/guide-map.md`
- Do not shorten, guess, or rewrite article slugs
- Use the official article title exactly as written in `references/guide-map.md`

### 5. Stay advisory by default

Unless the user explicitly asks for drafting help:

- do not write a full `CONTRIBUTING.md`
- do not write a governance charter
- do not write a code of conduct
- do not generate a full legal policy

If the user does ask for an artifact, say which guide(s) you are basing it on and then draft only the requested artifact.

## Routing Heuristics

Reach for these patterns first:

- Launch decision, project scope, expectations, readiness: `starting-a-project`
- How newcomers can help, contribution flow, first PR path: `how-to-contribute`
- Adoption, awareness, project discovery: `finding-users`
- Welcoming environment, community participation, contributor experience: `building-community`
- Maintainer workload, process clarity, saying no, automation: `best-practices`
- Shared decision-making, leadership models, formal rules: `leadership-and-governance`
- Sustainability, sponsorship, funding models: `getting-paid`
- Behavior expectations and enforcement norms: `code-of-conduct`
- Measuring health and progress: `metrics`
- Licensing and legal basics: `legal`
- Burnout, boundaries, maintainership balance: `maintaining-balance-for-open-source-maintainers`
- Security hygiene, project trust, dependency and vulnerability practices: `security-best-practices-for-your-project`

Common pairings:

- First launch + adoption: `starting-a-project` + `finding-users`
- Contributor growth + community experience: `how-to-contribute` + `building-community`
- Maintainer overload + burnout: `best-practices` + `maintaining-balance-for-open-source-maintainers`
- Governance + conduct expectations: `leadership-and-governance` + `code-of-conduct`
- Trust + sustainability for mature projects: `security-best-practices-for-your-project` + `best-practices` or `getting-paid`

Canonical title reminders:

- `starting-a-project` -> `Starting an Open Source Project`
- `code-of-conduct` -> `Your Code of Conduct`
- `security-best-practices-for-your-project` -> `Security Best Practices for your Project`

## Response Contract

Always use this structure:

Respond in plain Markdown only.

- Do not emit pseudo-tool calls
- Do not emit XML-like tags
- Do not emit internal reasoning markers
- Do not rename the section headings below
- If you begin responding, complete all five sections
- Never return empty wrappers, placeholders, or partial scaffolding

## Situation

State the inferred persona, project stage, and main challenge in plain language. If you made an assumption, note it in one sentence.

## Relevant Guides

List `1-3` guides. For each one include:

- official title copied exactly from `references/guide-map.md`, including capitalization
- why it applies here
- official URL

Preferred format:

`**Official Title**`

`Why it applies: ...`

`URL: <https://opensource.guide/...>`

## Recommended Next Steps

Provide a prioritized numbered list. Keep it concrete and proportionate to the user's scale.

## Watch-outs

Call out risks, anti-patterns, or ways the user could over-process the problem.

## Optional deeper reading

Include any extra guide links only if they are genuinely useful. If not, say that the guides above are enough for now.

Mini example:

## Situation

You are an early-stage solo maintainer deciding whether your side project is ready for open source.

## Relevant Guides

**Starting an Open Source Project**

Why it applies: It helps you decide whether to launch now and what basics to prepare first.

URL: <https://opensource.guide/starting-a-project/>

## Recommended Next Steps

1. Clarify the project scope and your maintenance boundaries.
2. Add a license, README, and minimal contributor expectations.
3. Share with a small early audience before a broader announcement.

## Watch-outs

Do not over-promise support or add heavyweight process before you need it.

## Optional deeper reading

If you want to think about early contributor experience, read How to Contribute to Open Source next.

## Quality Bar

Your answer should:

- sound like coaching, not policy boilerplate
- reflect the likely persona and maturity level
- use official guide links, not third-party summaries
- avoid presenting legal content as legal advice
- avoid copying long passages from the source material
- leave the user with a clear next move

## Escalation Rules

Escalate carefully when:

- the user is asking for legal certainty rather than general guidance
- the user needs incident response or code-level security help
- the user wants formal governance that may be disproportionate for a tiny project
- the user is clearly burned out and needs boundaries more than process

In those cases, keep the recommendation practical and say what this skill can and cannot confidently cover.
