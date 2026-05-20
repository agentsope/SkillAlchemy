#!/usr/bin/env python3
"""
Score a SKILL.md against the 13-point mechanical quality rubric.

Usage:
    python3 score_skill.py --skill <path>/SKILL.md          # single file
    python3 score_skill.py --skill <path>/SKILL.md --json   # JSON output
    python3 score_skill.py --dir <path>/skills/              # batch directory

The 13-point mechanical rubric is derived from statistical analysis of 477 skills
on skills.sh. See references/skill-grammar.md for methodology.

Note: This is the MECHANICAL score (max 13), distinct from the Stage 7
compilation SELF-ASSESSMENT score (max 10). The mechanical score is used
for runtime quality filtering (A-Stage 5 / B-Step 1). The self-assessment
is used after compilation to validate the output.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def score_skill(skill_path: Path) -> dict:
    """Score a single SKILL.md and return breakdown."""
    if not skill_path.exists():
        return {"error": "file not found", "path": str(skill_path)}

    text = skill_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    body_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    line_count = len(lines)

    score = 0
    strengths = []
    weaknesses = []

    # 1. frontmatter has name (1 pt)
    has_name = bool(re.search(r"^name:\s*\S", text, re.MULTILINE))
    if has_name:
        score += 1
        strengths.append("has_frontmatter_name")
    else:
        weaknesses.append("missing_frontmatter_name")

    # 2. frontmatter has description (1 pt)
    has_desc = bool(re.search(r"^description:\s*", text, re.MULTILINE))
    if has_desc:
        score += 1
        strengths.append("has_description")
    else:
        weaknesses.append("missing_description")

    # 3. description contains trigger words (2 pts, weighted)
    desc_match = re.search(r"^description:\s*(.+?)(?=\n\S|\n$|\Z)", text, re.MULTILINE | re.DOTALL)
    desc_text = desc_match.group(1) if desc_match else ""
    trigger_keywords = [
        "use when", "Use when", "触发", "when user", "when the user",
        "trigger", "activates when", "适用场景", "applies when"
    ]
    has_trigger = any(kw.lower() in desc_text.lower() for kw in trigger_keywords)
    if has_trigger:
        score += 2
        strengths.append("description_has_trigger")
    else:
        weaknesses.append("description_missing_trigger")

    # 4. description is specific (>80 chars) (1 pt)
    if len(desc_text.strip()) > 80:
        score += 1
        strengths.append("description_specific")
    else:
        weaknesses.append("description_too_vague")

    # 5. >=3 major sections (1 pt)
    h2_count = len(re.findall(r"^##\s+", text, re.MULTILINE))
    h3_count = len(re.findall(r"^###\s+", text, re.MULTILINE))
    if h2_count + h3_count >= 3:
        score += 1
        strengths.append("has_multiple_sections")
    else:
        weaknesses.append("too_few_sections")

    # 6. has boundary declaration (2 pts, weighted)
    boundary_patterns = [
        r"boundary", r"boundaries", r"边界", r"限制", r"不适用",
        r"limitations?", r"constraints", r"out of scope", r"适用范围外",
        r"boundary rules", r"boundary rule"
    ]
    has_boundary = any(re.search(p, text, re.IGNORECASE) for p in boundary_patterns)
    if has_boundary:
        score += 2
        strengths.append("has_boundary_section")
    else:
        weaknesses.append("missing_boundary")

    # 7. >=5 concrete steps (2 pts, weighted)
    step_patterns = [
        r"step\s*\d", r"Step\s*\d", r"phase\s*\d", r"Phase\s*\d",
        r"^\d+\.\s", r"步骤\s*\d",
    ]
    step_count = 0
    for pat in step_patterns:
        step_count += len(re.findall(pat, text, re.MULTILINE))
    if step_count >= 5:
        score += 2
        strengths.append("has_concrete_steps")
    else:
        weaknesses.append("insufficient_steps")

    # 8. has examples section (1 pt)
    has_examples = bool(re.search(
        r"example|示例|demo|用法示例|conversation|scenario",
        text, re.IGNORECASE
    ))
    if has_examples:
        score += 1
        strengths.append("has_examples_section")
    else:
        weaknesses.append("missing_examples")

    # 9. line count 100-400 (1 pt)
    if 100 <= line_count <= 400:
        score += 1
        strengths.append("line_count_sweet_spot")
    else:
        weaknesses.append(f"line_count_{line_count}")

    # 10. has references/related section (1 pt)
    has_refs = bool(re.search(
        r"reference|参考|参见|see also|related|相关",
        text, re.IGNORECASE
    ))
    if has_refs:
        score += 1
        strengths.append("has_references_section")
    else:
        weaknesses.append("missing_references")

    # 11. penalty: <30 lines (-2 pts)
    if line_count < 30:
        score -= 2
        weaknesses.append("too_thin_penalty")

    # Determine grade
    if score >= 11:
        grade = "elite"
    elif score >= 9:
        grade = "standard"
    else:
        grade = "draft"

    # Determine skill mode
    persona_signals = ["角色扮演", "我怎么说话", "我绝不会说", "标志句式",
                       "我看世界的方式", "决策启发式", "persona"]
    skill_mode = "persona" if any(s in text for s in persona_signals) else "tool"

    return {
        "path": str(skill_path),
        "score": min(score, 13),
        "max": 13,
        "grade": grade,
        "skill_mode": skill_mode,
        "line_count": line_count,
        "strengths": strengths,
        "weaknesses": weaknesses,
    }


def main():
    parser = argparse.ArgumentParser(description="Score SKILL.md files")
    parser.add_argument("--skill", type=Path, help="Path to SKILL.md")
    parser.add_argument("--dir", type=Path, help="Path to directory of SKILL.md files")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.skill:
        result = score_skill(args.skill)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"{result['path']}: {result['score']}/13 ({result['grade']}) — {result['skill_mode']}")
            if result.get("strengths"):
                print(f"  ✓ {', '.join(result['strengths'])}")
            if result.get("weaknesses"):
                print(f"  ✗ {', '.join(result['weaknesses'])}")

    elif args.dir:
        results = []
        for md in sorted(args.dir.glob("**/SKILL.md")):
            results.append(score_skill(md))
        results.sort(key=lambda r: r["score"], reverse=True)

        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            for r in results:
                print(f"[{r['score']:2}/13 {r['grade']:8s}] {r['skill_mode']:6s} {r['path']}")
            elite = sum(1 for r in results if r["grade"] == "elite")
            standard = sum(1 for r in results if r["grade"] == "standard")
            draft = sum(1 for r in results if r["grade"] == "draft")
            print(f"\n{len(results)} skills: {elite} elite, {standard} standard, {draft} draft")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
