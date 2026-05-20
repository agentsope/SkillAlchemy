#!/usr/bin/env python3
"""
Mechanical quality scorer — deterministic scoring across domain confidence,
operation coverage, evidence binding, taxonomy alignment, specificity balance,
and agentic protocol. Also validates generated SKILL.md files for Entry B.

Usage:
    python3 scripts/quality_check.py --skill output/example-skill/SKILL.md
    python3 scripts/quality_check.py --skill output/莫言-skill/SKILL.md
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CONFIDENCE_SCORES = {
    "high": 20,
    "medium": 14,
    "low": 6,
    "": 4,
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def operations(discovery: dict[str, object]) -> list[dict[str, object]]:
    items = discovery.get("operations", [])
    return [item for item in items if isinstance(item, dict)]


def evidence_items(operation: dict[str, object]) -> list[dict[str, object]]:
    evidence = operation.get("evidence", [])
    return [item for item in evidence if isinstance(item, dict)]


def domain_confidence_score(classification: dict[str, object]) -> tuple[int, list[str]]:
    confidence = str(classification.get("confidence", "")).lower()
    score = CONFIDENCE_SCORES.get(confidence, 4)
    warnings = []
    if confidence != "high":
        warnings.append(f"domain_confidence_{confidence or 'unknown'}")
    return score, warnings


def operation_coverage_score(found_operations: list[dict[str, object]]) -> tuple[int, list[str]]:
    count = len(found_operations)
    if count >= 6:
        return 20, []
    if count >= 4:
        return 15, ["operation_count_medium"]
    if count >= 2:
        return 8, ["operation_count_low"]
    return 0, ["operation_count_critical"]


def evidence_coverage_score(found_operations: list[dict[str, object]]) -> tuple[int, list[str]]:
    if not found_operations:
        return 0, ["no_operations_for_evidence"]

    with_evidence = 0
    empty_snippets = 0
    for operation in found_operations:
        items = evidence_items(operation)
        if items:
            with_evidence += 1
            if not str(items[0].get("snippet", "")).strip():
                empty_snippets += 1

    ratio = with_evidence / len(found_operations)
    score = round(ratio * 20)
    warnings = []
    if ratio < 1:
        warnings.append("missing_operation_evidence")
    if empty_snippets:
        warnings.append("empty_evidence_snippet")
        score = max(0, score - min(5, empty_snippets))
    return score, warnings


def taxonomy_alignment_score(candidate: dict[str, object], found_operations: list[dict[str, object]]) -> tuple[int, list[str]]:
    candidate_families = {str(item).lower() for item in candidate.get("candidate_operation_families", [])}
    if not candidate_families:
        return 5, ["candidate_taxonomy_missing"]

    operation_families = {str(item.get("operation_family", "")).lower() for item in found_operations}
    matched = {family for family in operation_families if family in candidate_families}
    if not operation_families:
        return 0, ["no_operation_family_alignment"]

    ratio = len(matched) / len(operation_families)
    score = round(ratio * 15)
    warnings = []
    if ratio < 0.5:
        warnings.append("weak_taxonomy_alignment")
    return score, warnings


def specificity_balance_score(run_dir: Path, found_operations: list[dict[str, object]]) -> tuple[int, list[str]]:
    warnings = []
    exact_path_hits = 0
    for operation in found_operations:
        for value in operation.get("input_needed", []):
            if str(value).startswith("environment/"):
                exact_path_hits += 1

    score = 15
    if exact_path_hits > 0:
        warnings.append("task_specific_paths_in_intermediate")
        score -= min(5, exact_path_hits)

    plan_path = run_dir / "skill_generation_plan.md"
    if plan_path.exists():
        text = plan_path.read_text(encoding="utf-8")
        if "exact input file paths" not in text or "environment/skills" not in text:
            warnings.append("specificity_boundary_weak")
            score -= 5
    return max(0, score), warnings


def agentic_protocol_score(run_dir: Path) -> tuple[int, list[str]]:
    task_sop = run_dir / "task_sop.md"
    plan = run_dir / "skill_generation_plan.md"
    text = ""
    if task_sop.exists():
        text += task_sop.read_text(encoding="utf-8")
    if plan.exists():
        text += "\n" + plan.read_text(encoding="utf-8")

    required_markers = [
        "Source-Derived Workflow",
        "Core Operations To Generalize",
        "Must Not Use",
        "Publish Boundary",
    ]
    missing = [marker for marker in required_markers if marker not in text]
    score = 10 - (2 * len(missing))
    warnings = [f"missing_{marker.lower().replace(' ', '_')}" for marker in missing]
    return max(0, score), warnings


def multi_domain_notes(classification: dict[str, object]) -> list[str]:
    secondary = classification.get("secondary_domains", [])
    if isinstance(secondary, list) and secondary:
        return [f"secondary_domain:{domain}" for domain in secondary]
    return []


def classify_quality(score: int, warnings: list[str]) -> str:
    critical = {"operation_count_critical", "no_operations_for_evidence", "empty_evidence_snippet"}
    if critical.intersection(warnings):
        return "fail"
    if any(warning.startswith("domain_confidence_low") for warning in warnings):
        return "usable_with_warnings" if score >= 65 else "weak"
    if score >= 80:
        return "strong"
    if score >= 65:
        return "usable_with_warnings" if warnings else "strong"
    if score >= 50:
        return "weak"
    return "fail"


def build_quality_report(run_dir: Path) -> dict[str, object]:
    classification = load_json(run_dir / "domain_classification.json")
    candidate = load_json(run_dir / "candidate_taxonomy.json")
    discovery = load_json(run_dir / "operation_discovery.json")
    found_operations = operations(discovery)

    components: list[dict[str, object]] = []
    warnings: list[str] = []

    for name, value in [
        ("domain_confidence", domain_confidence_score(classification)),
        ("operation_coverage", operation_coverage_score(found_operations)),
        ("evidence_coverage", evidence_coverage_score(found_operations)),
        ("taxonomy_alignment", taxonomy_alignment_score(candidate, found_operations)),
        ("specificity_balance", specificity_balance_score(run_dir, found_operations)),
        ("agentic_protocol", agentic_protocol_score(run_dir)),
    ]:
        score, component_warnings = value
        components.append({"name": name, "score": score, "warnings": component_warnings})
        warnings.extend(component_warnings)

    score = sum(int(component["score"]) for component in components)
    notes = multi_domain_notes(classification)
    quality_status = classify_quality(score, warnings)
    return {
        "schema_version": "0.1.0",
        "task": run_dir.name,
        "quality_score": score,
        "quality_status": quality_status,
        "publishable": quality_status in {"strong", "usable_with_warnings"},
        "warnings": warnings,
        "notes": notes,
        "components": components,
        "domain": classification.get("primary_domain", "mixed"),
        "subdomain": classification.get("subdomain", ""),
        "operation_count": len(found_operations),
    }


TOOL_MODE_SECTIONS = [
    "Activation Rules",
    "Agentic Protocol",
    "Operation Models",
    "Output Style",
    "Boundary Rules",
    "Output Modes",
    "References",
]

PERSONA_MODE_SECTIONS = [
    "角色扮演规则",
    "身份",
    "我看世界的方式",
    "我怎么说话",
    "决策启发式",
    "运行时协议",
    "边界",
    "参考",
]

# Content-level checks for persona mode (orchestrator Phase 8 pre-screening).
# These run AFTER section presence check. Warnings here do NOT block publish —
# agent-driven Phase 8 content validation is the final gate.
PERSONA_CONTENT_CHECKS = {
    "forbidden_phrases": {
        "pattern": "我绝不会说",
        "section": "我怎么说话",
        "label": "「我绝不会说」in 我怎么说话",
    },
    "signature_line": {
        "pattern": "我的标志句式",
        "section": "我怎么说话",
        "label": "「我的标志句式」in 我怎么说话",
    },
    "research_before_answer": {
        "pattern": "调研先行|WebSearch|先搜|Read.*sop_models",
        "section": "运行时协议",
        "label": "「调研先行 / Read SOP」in 运行时协议",
    },
    "decision_heuristics_count": {
        "pattern": None,  # special: count bullet/num items in 决策启发式 section
        "section": "决策启发式",
        "label": "≥3 条决策启发式",
        "min_count": 3,
    },
}

TOOL_MODE_ALIASES = {
    "Operation Models": ["Operation Models", "Core Operation Models"],
    "Boundary Rules": ["Boundary Rules", "边界规则"],
    "References": ["References", "参考"],
}

PERSONA_MODE_ALIASES = {
    "参考": ["参考", "References"],
    "边界": ["边界", "Boundary Rules", "Boundary"],
}


def detect_skill_mode(text: str) -> str:
    """Detect whether the SKILL.md is persona mode or tool mode."""
    if "角色扮演规则" in text or "## 身份" in text:
        return "persona"
    if "## Activation Rules" in text or "## Agentic Protocol" in text:
        return "tool"
    # Heuristic: Chinese section headers suggest persona
    chinese_sections = ["角色扮演规则", "身份", "我看世界的方式", "我怎么说话"]
    if sum(1 for s in chinese_sections if f"## {s}" in text) >= 2:
        return "persona"
    return "tool"


def check_section_present(text: str, section: str, aliases: dict[str, list[str]] | None = None) -> bool:
    """Check if a section (or any of its aliases) is present in the text."""
    names = [section]
    if aliases and section in aliases:
        names.extend(aliases[section])
    return any(f"## {name}" in text for name in names)

FORBIDDEN_PATTERNS = [
    ("write exactly as", "living_author_impersonation"),
    ("copy.*protected expression", "copyright_bypass"),
    ("pretend to be", "living_author_impersonation"),
    ("environment/skills", "benchmark_leakage_path"),
    ("solution/", "benchmark_leakage_path"),
]


def check_skill_file(skill_path: Path) -> dict[str, object]:
    if not skill_path.exists():
        return {"status": "fail", "reason": "SKILL.md not found", "path": skill_path.as_posix()}

    # Check if this is an engine/orchestrator SKILL.md (not a generated output skill).
    # Engine/orchestrator skills have their own structure and should not be
    # validated against the persona/tool output templates.
    skill_json_path = skill_path.parent / "skill.json"
    if skill_json_path.exists():
        try:
            meta = json.loads(skill_json_path.read_text(encoding="utf-8"))
            if meta.get("type") in ("engine", "orchestrator"):
                return {
                    "status": "pass",
                    "path": skill_path.as_posix(),
                    "line_count": len(skill_path.read_text(encoding="utf-8").split("\n")),
                    "skill_mode": meta.get("type", "engine"),
                    "missing_sections": [],
                    "content_warnings": [],
                    "forbidden_pattern_hits": [],
                    "skill_json_valid": True,
                    "publishable": True,
                    "note": f"Engine/orchestrator SKILL.md — skipped output-template validation"
                }
        except (json.JSONDecodeError, KeyError):
            pass  # Fall through to normal validation

    text = skill_path.read_text(encoding="utf-8")
    mode = detect_skill_mode(text)

    if mode == "persona":
        required = PERSONA_MODE_SECTIONS
        aliases = PERSONA_MODE_ALIASES
    else:
        required = TOOL_MODE_SECTIONS
        aliases = TOOL_MODE_ALIASES

    missing_sections = [
        section for section in required
        if not check_section_present(text, section, aliases)
    ]

    # Content-level checks (warnings, not blocking — agent-driven Phase 8 is final gate)
    content_warnings: list[dict[str, str]] = []
    if mode == "persona":
        for check_id, spec in PERSONA_CONTENT_CHECKS.items():
            section_text = _extract_section_text(text, spec["section"])
            if not section_text:
                content_warnings.append({"check": check_id, "label": spec["label"], "result": "section_not_found"})
                continue
            if check_id == "decision_heuristics_count":
                # Count heuristic entries: bullet lines, numbered lines, bold-prefixed,
                # Chinese pattern like "出手前三问：..." (keyword followed by ：),
                # or em-dash pattern like "规则名 — 描述" / "规则名——描述"
                items_bullet = re.findall(r"(?:^[-*]\s|^\d+\.|^\*\*)", section_text, re.MULTILINE)
                items_chinese = re.findall(r"^[^\n]{2,8}[：—][^\n]{10,}", section_text, re.MULTILINE)
                items_emdash = re.findall(r"^[^\n]{3,20}\s[—]\s[^\n]{10,}", section_text, re.MULTILINE)
                count = len(items_bullet) + len(items_chinese) + len(items_emdash)
                if count < spec.get("min_count", 3):
                    content_warnings.append({
                        "check": check_id, "label": spec["label"],
                        "result": f"found_{count}_need_{spec['min_count']}"
                    })
            else:
                if spec["pattern"] and not re.search(spec["pattern"], section_text):
                    content_warnings.append({"check": check_id, "label": spec["label"], "result": "missing"})

    forbidden_hits = [
        {"pattern": pattern, "tag": tag}
        for pattern, tag in FORBIDDEN_PATTERNS
        if re.search(pattern, text, re.IGNORECASE) and not _is_allowed_boundary(pattern, text)
    ]
    line_count = len(text.splitlines())

    skill_json_path = skill_path.parent / "skill.json"
    json_valid = False
    if skill_json_path.exists():
        try:
            json.loads(skill_json_path.read_text(encoding="utf-8"))
            json_valid = True
        except (json.JSONDecodeError, ValueError):
            pass

    all_checks_pass = not missing_sections and not forbidden_hits and json_valid
    return {
        "status": "pass" if all_checks_pass else "fail",
        "path": skill_path.as_posix(),
        "line_count": line_count,
        "skill_mode": mode,
        "missing_sections": missing_sections,
        "content_warnings": content_warnings,
        "forbidden_pattern_hits": forbidden_hits,
        "skill_json_valid": json_valid,
        "publishable": all_checks_pass,
    }


def _extract_section_text(text: str, section_name: str) -> str:
    """Extract the body text of a markdown section by its ## heading."""
    pattern = rf"^##\s+{re.escape(section_name)}\s*$([\s\S]*?)(?=^##\s+|\Z)"
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _is_allowed_boundary(pattern: str, text: str) -> bool:
    # Patterns like "Do not copy protected expression" in Boundary Rules are allowed —
    # they are the guardrails themselves, not violations.
    boundary_section_match = re.search(r"## Boundary Rules\s*\n([\s\S]*?)(?=^## |\Z)", text, re.MULTILINE)
    if boundary_section_match:
        boundary_text = boundary_section_match.group(1)
        if re.search(pattern, boundary_text, re.IGNORECASE):
            return True
    return False


def write_quality_report(run_dir: Path) -> Path:
    report = build_quality_report(run_dir)
    output_path = run_dir / "quality_report.json"
    write_json(output_path, report)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="Path to a SKILL.md file (with --skill)")
    parser.add_argument("--skill", action="store_true", help="Validate a generated SKILL.md file directly (Entry B).")
    args = parser.parse_args()

    target = Path(args.target)
    if args.skill:
        result = check_skill_file(target)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "pass" else 1
    output_path = write_quality_report(target)
    print(f"Wrote quality report: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
