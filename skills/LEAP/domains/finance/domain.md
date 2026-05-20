# Finance Domain Pack

Purpose:
extract SOPs for financial analysis, filings, valuation, portfolio, risk,
market research, and reporting.

Common sources:
SEC filings, holdings data, spreadsheets, market data, research notes, PDFs.

Candidate operation families:
entity resolution, data extraction, reconciliation, metric calculation,
ranking, valuation, risk check, report.

Validation focus:
source period, units, identifiers, calculations, no investment advice beyond
task scope.

Research dimensions (for subagent planning — source modality × evidence depth):
- financial_analysis: ratio computation, trend analysis, benchmarking, statement interpretation
- valuation: model selection, assumption validation, sensitivity analysis, comparables
- risk_assessment: exposure quantification, stress testing, scenario modeling
- regulatory_compliance: filing requirements, disclosure patterns, audit trail conventions
- data_reconciliation: ledger verification, transaction matching, period alignment
- portfolio_construction: allocation logic, rebalancing rules, constraint handling

Cross-domain bridges (commonly intersecting domains, and what to borrow):
- mathematics: borrow optimization_modeling (portfolio optimization), proof_strategy (arbitrage-free reasoning)
- office-white-collar: borrow document_structure (financial reporting format), compliance_checking (regulatory filings)
- software-engineering: borrow debugging_patterns (audit investigation), code_architecture (quant/system structure)

Dimension derivation hints (when source evidence suggests a dimension not on the menu):
- source involves macro or central bank analysis → derive `macro_regime_analysis` dimension
- source involves behavioral / psychological factors → derive `behavioral_edge` dimension
- source involves illiquid or private assets → derive `illiquid_valuation` dimension
- new dimension rule: name = `<operation_the_source_exposes>`, mission = "extract how <target> performs <operation>"

