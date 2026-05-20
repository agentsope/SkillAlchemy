# Mathematics Domain Pack

Purpose:
extract SOPs for proofs, formal methods, problem solving, symbolic reasoning,
optimization, and numerical verification.

Common sources:
problem statements, LaTeX, Lean files, lecture notes, proof sketches, solver
models.

Candidate operation families:
inspect input, parse artifacts/data, formalize problem, formalize problem
model, introduce definitions, choose strategy, solve or prove, prove lemmas,
split cases, calculate, optimize, verify, validate, report, generalize.

Validation focus:
logical completeness, symbol consistency, proof checking, no hidden assumption,
no theorem statement modification.

Research dimensions (for subagent planning — source modality × evidence depth):
- problem_formalization: definition crafting, assumption articulation, notation standardization
- proof_strategy: induction, contradiction, construction, case analysis, diagonalization
- symbolic_manipulation: algebraic transformation, inequality handling, pattern recognition
- optimization_modeling: objective formulation, constraint encoding, solver selection
- generalization: from specific case to general theorem, boundary identification
- verification: proof checking, counterexample search, edge case enumeration

Cross-domain bridges (commonly intersecting domains, and what to borrow):
- software-engineering: borrow debugging_patterns (proof debugging), code_architecture (proof structure ≈ code structure)
- natural-science: borrow model_building (mathematical modeling), limitation_articulation (axiom boundary)
- finance: borrow risk_assessment (probabilistic reasoning), portfolio_construction (constrained optimization)

Dimension derivation hints (when source evidence suggests a dimension not on the menu):
- source involves computational / algorithmic methods → derive `algorithm_design` dimension
- source involves teaching or exposition of mathematics → derive `mathematical_exposition` dimension
- source spans multiple subfields or analogical transfer → derive `cross_domain_transfer` dimension
- new dimension rule: name = `<operation_the_source_exposes>`, mission = "extract how <target> performs <operation>"
