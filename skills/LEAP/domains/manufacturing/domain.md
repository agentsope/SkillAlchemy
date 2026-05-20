# Manufacturing Domain Pack

Purpose:
extract SOPs for CAD/CAM, 3D scanning, mesh inspection, process control,
equipment maintenance, quality assurance, and production optimization.

Common sources:
STL/DXF/CAD files, equipment logs, QC reports, maintenance records, process
data, material tables.

Candidate operation families:
inspect input, parse artifacts/data, parse geometry/process data, filter noise,
filter/select relevant entity, measure, lookup reference data, lookup
material/process constraints, calculate, validate, report.

Validation focus:
units, tolerances, material properties, largest component/noise filtering,
process constraints, no hardcoded benchmark answer.

Research dimensions (for subagent planning — source modality × evidence depth):
- geometry_parsing: CAD/STL interpretation, mesh analysis, feature extraction, binary format handling
- tolerance_analysis: precision requirements, quality gates, GD&T, measurement uncertainty
- material_handling: density/property lookup, process constraints, material selection logic
- process_planning: operation sequencing, tool selection, workflow optimization
- quality_assurance: inspection methods, statistical process control, defect classification
- output_schema: deliverable format conventions, report structure, validation rules

Cross-domain bridges (commonly intersecting domains, and what to borrow):
- robotics: borrow motion_planning (toolpath ≈ motion), sensor_fusion (multi-sensor QC), failure_diagnosis
- software-engineering: borrow ci_deployment (manufacturing pipeline), testing_strategy (QC ≈ testing)
- mathematics: borrow optimization_modeling (process optimization), generalization (from one part to family)

Dimension derivation hints (when source evidence suggests a dimension not on the menu):
- source involves additive/subtractive process choice → derive `process_selection` dimension
- source involves supply chain or vendor qualification → derive `supply_chain_quality` dimension
- source spans design-for-manufacturing feedback → derive `dfm_feedback` dimension
- new dimension rule: name = `<operation_the_source_exposes>`, mission = "extract how <target> performs <operation>"
