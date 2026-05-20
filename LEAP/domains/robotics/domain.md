# Robotics Domain Pack

Purpose:
extract SOPs for planning, control, perception, simulation, calibration, and
robotic failure diagnosis.

Common sources:
simulation files, logs, robot configs, sensor data, control models, papers.

Candidate operation families:
inspect input, parse artifacts/data, state estimation, planning, control,
constraint handling, simulation, calculate, metrics, validate, report, failure
diagnosis.

Validation focus:
dynamics consistency, safety constraints, simulation metrics, no unsupported
real-world deployment claims.

Research dimensions (for subagent planning — source modality × evidence depth):
- motion_planning: path planning, collision avoidance, trajectory optimization
- control_systems: feedback loops, PID tuning, state estimation, stability analysis
- sensor_fusion: multi-sensor integration, noise filtering, calibration procedures
- simulation_validation: sim-to-real transfer, fidelity assessment, domain randomization
- failure_diagnosis: anomaly detection, root cause analysis, recovery procedures
- safety_engineering: constraint enforcement, emergency stop logic, redundancy patterns

Cross-domain bridges (commonly intersecting domains, and what to borrow):
- manufacturing: borrow process_planning (assembly sequence), quality_assurance (validation)
- software-engineering: borrow code_architecture (ROS node structure), ci_deployment (simulation pipeline)
- mathematics: borrow optimization_modeling (trajectory optimization), problem_formalization (dynamics)

Dimension derivation hints (when source evidence suggests a dimension not on the menu):
- source involves human-robot interaction → derive `hri_design` dimension
- source involves multi-robot coordination → derive `swarm_coordination` dimension
- source spans hardware-software co-design → derive `hw_sw_codesign` dimension
- new dimension rule: name = `<operation_the_source_exposes>`, mission = "extract how <target> performs <operation>"
