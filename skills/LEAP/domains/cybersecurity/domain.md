# Cybersecurity Domain Pack

Purpose:
extract SOPs for threat detection, incident response, vulnerability analysis,
traffic analysis, hardening, and security testing.

Common sources:
pcap, logs, CVE, exploit notes, detection rules, SIEM exports, incident reports.

Candidate operation families:
collect evidence, inspect input, parse artifacts, parse artifacts/data,
parse security artifacts, detect indicators, correlate events, correlate
indicators, assess risk, respond, verify, validate, report, harden.

Validation focus:
no fabricated exploitability, clear evidence chain, false-positive handling,
safe defensive framing.

Research dimensions (for subagent planning — source modality × evidence depth):
- threat_detection: indicator patterns, anomaly identification, signature design, IoC extraction
- incident_response: triage procedures, containment strategies, eradication, recovery workflows
- vulnerability_analysis: exploitation patterns, severity assessment, attack surface mapping
- traffic_analysis: protocol parsing, flow patterns, exfiltration detection, PCAP inspection
- security_hardening: configuration standards, patching logic, defense-in-depth patterns
- forensic_investigation: evidence collection, timeline reconstruction, attribution

Cross-domain bridges (commonly intersecting domains, and what to borrow):
- software-engineering: borrow debugging_patterns (vuln hunting ≈ debugging), ci_deployment (patching pipeline)
- finance: borrow risk_assessment (quantifying threat exposure), regulatory_compliance (audit frameworks)
- media-content-production: borrow voice_and_style for security communication / awareness content

Dimension derivation hints (when source evidence suggests a dimension not on the menu):
- source contains "responsible disclosure" or "bug bounty" patterns → derive `coordinated_disclosure` dimension
- source contains adversarial simulation (red team / purple team) → derive `adversarial_emulation` dimension
- source spans geopolitical or APT attribution → derive `threat_actor_profiling` dimension
- new dimension rule: name = `<operation_the_source_exposes>`, mission = "extract how <target> performs <operation>"
