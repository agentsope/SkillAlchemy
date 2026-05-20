# Office & White Collar Domain Pack

Purpose:
extract SOPs for business documents, email, spreadsheets, slides, forms,
reports, meeting workflows, and knowledge work.

Common sources:
DOCX, XLSX, PPTX, PDF forms, email threads, meeting notes, business reports.

Candidate operation families:
intake, inspect input, extract requirements, extract document requirements,
parse artifacts/data, lookup reference data, reconcile data, calculate,
transform document, transform and review document, format, review, validate,
report, deliver.

Validation focus:
format fidelity, data correctness, document constraints, no unsupported business
claims.

Research dimensions (for subagent planning — source modality × evidence depth):
- document_structure: template conventions, section patterns, formatting rules
- data_reconciliation: cross-checking logic, formula validation, consistency verification
- review_workflow: approval chains, revision tracking, sign-off patterns
- compliance_checking: regulatory mapping, audit trail requirements, exception handling
- communication_patterns: email/meeting conventions, escalation rules, stakeholder mapping
- tool_usage: spreadsheet formulas, document automation, data transformation patterns

Cross-domain bridges (commonly intersecting domains, and what to borrow):
- finance: borrow financial_analysis (business reporting), regulatory_compliance (SOX, audit)
- software-engineering: borrow debugging_patterns (process troubleshooting), ci_deployment (approval pipeline ≈ CI)
- media-content-production: borrow content_strategy (internal communications), voice_and_style (executive reporting tone)

Dimension derivation hints (when source evidence suggests a dimension not on the menu):
- source involves meeting facilitation or decision-making process → derive `decision_governance` dimension
- source involves knowledge management or institutional memory → derive `knowledge_capture` dimension
- source spans cross-functional coordination → derive `cross_functional_orchestration` dimension
- new dimension rule: name = `<operation_the_source_exposes>`, mission = "extract how <target> performs <operation>"
