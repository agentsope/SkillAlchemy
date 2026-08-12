# Changelog

## Unreleased

**Paper-aligned method implementation**

- Reframed SkillAlchemy as three stages: implicit requirement discovery,
  evidence-grounded procedure admission, and skill package compilation
- Added paired contrast records for component-level treatment changes
- Made research questions, matched contexts, and source-access limits explicit in
  the research-plan artifact
- Added explicit General, Scoped, and Exclude admission records
- Preserved source-stated applicability boundaries and condition-specific cases
- Separated research evidence merging from procedure induction and admission
- Added the corpus integrity filter described in the paper and support for
  multi-line YAML descriptions
- Added optional `scripts/` and `assets/` to the compiled package design
- Removed the unsupported post-compilation validation, repair, and self-evaluation pipeline
- Converted the SkillAlchemy, Lens, LEAP, and technical documentation content to English

## v1.0

First public release.

**Architecture**
- Skill-Alchemy orchestrator: Phase 0-4 pipeline with CLI interaction UI
- Lens cognitive lens: 4-step cognitive expansion, zero interaction
- LEAP execution engine: A-branch distill (7 Stage + 2 Gate) + B-branch fuse (4 Step + 3 Gate)

**Core innovations**
- skill-grammar: data-validated Skill writing rules from skills.sh
- score_skill: 13-point mechanical quality scoring, runtime filtering
- find-skills integration: real-time semantic search across all public Skills
- Quality pyramid: quantified elite/standard/draft tiers
- Dilemma Decision Cases: OS extraction from real decision moments
- Persona-OS cross-layer: 7 OS extraction dimensions

**Infrastructure**
- 12 domain packs + persona-os cross-layer
- quality_check: structural validation for generated Skills
- build_corpus / build_component_index: data mining tools (open-source build)
