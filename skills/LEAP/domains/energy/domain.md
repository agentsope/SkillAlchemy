# Energy Domain Pack

Purpose:
extract SOPs for power systems, dispatch, unit commitment, market pricing,
grid optimization, and energy system analysis.

Common sources:
network JSON, grid models, market data, load profiles, generator constraints,
technical reports.

Candidate operation families:
inspect input, parse artifacts/data, parse system data, formulate constraints,
formulate power-system constraints, optimize, solve energy optimization, check
feasibility, calculate, price, audit, validate, report.

Validation focus:
demand balance, reserve, generator limits, ramping, costs, feasibility, no
constraint omission.

Research dimensions (for subagent planning — source modality × evidence depth):
- load_forecasting: demand prediction, weather correlation, temporal decomposition
- dispatch_optimization: unit commitment, economic dispatch, constraint formulation
- grid_modeling: network topology, power flow analysis, contingency evaluation
- market_pricing: LMP calculation, bidding strategy, settlement patterns
- renewable_integration: variability handling, storage sizing, curtailment logic
- constraint_handling: ramping limits, transmission capacity, reserve requirements

Cross-domain bridges (commonly intersecting domains, and what to borrow):
- mathematics: borrow optimization_modeling (dispatch ≈ optimization problem), generalization (from single grid to N-region)
- finance: borrow portfolio_construction (generation portfolio ≈ asset allocation), risk_assessment (reliability risk)
- natural-science: borrow model_building for climate/weather integration, limitation_articulation for forecast uncertainty

Dimension derivation hints (when source evidence suggests a dimension not on the menu):
- source involves storage (battery/pumped hydro) scheduling → derive `storage_dispatch` dimension
- source involves demand response or consumer behavior → derive `demand_side_management` dimension
- source spans policy/carbon pricing → derive `policy_integration` dimension
- new dimension rule: name = `<operation_the_source_exposes>`, mission = "extract how <target> performs <operation>"
