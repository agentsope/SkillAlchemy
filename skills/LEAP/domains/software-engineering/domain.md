# Software Engineering Domain Pack

Purpose:
extract SOPs for code, debugging, builds, tests, architecture, dependency,
release, CI, and incident workflows.

Common sources:
repo, issue, PR, logs, CI output, README, docs, codebase, incident report.

Candidate operation families:
reproduce, inspect, inspect input, parse artifacts/data, model system inputs,
hypothesize, detect failure pattern, patch, apply system repair, test, regress,
lookup reference data, report, document, release.

Validation focus:
reproduction, root cause, tests, API compatibility, rollback, no invented code
behavior.

Research dimensions (for subagent planning — source modality × evidence depth):
- code_architecture: design patterns, module structure, dependency conventions
- api_contracts: endpoint signatures, error handling, versioning patterns
- testing_strategy: test patterns, coverage approach, mock/fixture conventions
- ci_deployment: build pipeline, release process, rollback patterns, environment management
- debugging_patterns: reproduction steps, root cause analysis, fix strategies, logging conventions
- dependency_management: library selection criteria, version pinning, vulnerability handling

Cross-domain bridges (commonly intersecting domains, and what to borrow):
- cybersecurity: borrow threat_detection (vuln scanning), incident_response (outage handling)
- mathematics: borrow problem_formalization (specification), proof_strategy (correctness reasoning)
- media-content-production: borrow content_strategy for tech blogging/devrel, voice_and_style for code review tone

Dimension derivation hints (when source evidence suggests a dimension not on the menu):
- source involves developer experience or tooling design → derive `dx_design` dimension
- source involves on-call / production operations → derive `production_operations` dimension
- source spans technical decision-making with tradeoffs → derive `tech_strategy` dimension
- new dimension rule: name = `<operation_the_source_exposes>`, mission = "extract how <target> performs <operation>"
