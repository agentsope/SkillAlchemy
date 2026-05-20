# Natural Science Domain Pack

Purpose:
extract SOPs for scientific analysis, papers, experiments, measurement,
simulation, and data interpretation.

Common sources:
papers, methods sections, lab notes, datasets, figures, model outputs, reports.

Candidate operation families:
research question, hypothesis, method selection, measurement, variable control,
analysis, anomaly handling, limitation, conclusion.

Validation focus:
evidence quality, variable control, uncertainty, reproducibility, no causal
overclaiming.

Research dimensions (for subagent planning — source modality × evidence depth):
- experimental_design: hypothesis formation, variable control, measurement protocol
- data_analysis: statistical methods, visualization patterns, interpretation heuristics
- literature_positioning: citation patterns, gap identification, contribution framing
- reproducibility: methods documentation, data availability, parameter reporting
- limitation_articulation: uncertainty quantification, boundary conditions, confounders
- model_building: assumption justification, simplification rationale, validation strategy

Cross-domain bridges (commonly intersecting domains, and what to borrow):
- mathematics: borrow proof_strategy (theorem-like reasoning), optimization_modeling (parameter fitting)
- software-engineering: borrow debugging_patterns (experiment debugging), testing_strategy (validation ≈ testing)
- media-content-production: borrow narrative_structure for science communication, voice_and_style for grant/manuscript writing

Dimension derivation hints (when source evidence suggests a dimension not on the menu):
- source involves meta-science or methodology critique → derive `methodology_critique` dimension
- source involves interdisciplinary bridging → derive `cross_disciplinary_integration` dimension
- source spans science policy or funding strategy → derive `science_strategy` dimension
- new dimension rule: name = `<operation_the_source_exposes>`, mission = "extract how <target> performs <operation>"

