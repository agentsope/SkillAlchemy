# Healthcare Domain Pack

Purpose:
extract SOPs for clinical guidelines, healthcare protocols, biomedical data
workflows, evidence review, and care process documents.

Common sources:
clinical guidelines, papers, protocols, de-identified datasets, lab reports,
workflow documents.

Candidate operation families:
evidence review, eligibility, risk check, decision pathway, contraindication,
monitoring, escalation, documentation.

Validation focus:
no diagnosis, no patient-specific medical advice, uncertainty, evidence level,
clinical boundary, safety disclaimers.

Research dimensions (for subagent planning — source modality × evidence depth):
- clinical_reasoning: evidence evaluation, differential pathways, guideline interpretation
- protocol_adherence: care pathway design, deviation documentation, compliance checking
- patient_safety: contraindication screening, drug interaction checking, monitoring triggers
- data_privacy: de-identification patterns, consent boundaries, regulatory mapping
- outcome_assessment: endpoint selection, measurement methodology, follow-up design
- documentation: clinical note structure, coding conventions, handoff patterns

Cross-domain bridges (commonly intersecting domains, and what to borrow):
- natural-science: borrow experimental_design (trial methodology), limitation_articulation (uncertainty communication)
- office-white-collar: borrow review_workflow (approval chains), compliance_checking (regulatory audit)
- cybersecurity: borrow threat_detection (patient safety event detection), forensic_investigation (adverse event analysis)

Dimension derivation hints (when source evidence suggests a dimension not on the menu):
- source involves shared decision-making or patient communication → derive `patient_communication` dimension
- source involves resource allocation / triage under constraint → derive `resource_stewardship` dimension
- source spans public health or population-level patterns → derive `population_health` dimension
- new dimension rule: name = `<operation_the_source_exposes>`, mission = "extract how <target> performs <operation>"

