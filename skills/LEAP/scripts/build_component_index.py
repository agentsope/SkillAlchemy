#!/usr/bin/env python3
"""
Build a component-level index of skill patterns for LEAP Stage 5.

Parses all SKILL.md files in corpus/skills/, extracts structural components
(trigger patterns, SOP types, operation types, section structures), and
builds a searchable JSON index.

Usage:
    python3 scripts/build_component_index.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "corpus" / "skills"
MANIFEST_PATH = ROOT / "corpus" / "manifest.json"
INDEX_PATH = ROOT / "references" / "component-index.json"
STATS_PATH = ROOT / "references" / "grammar-stats.json"


def parse_skill_md(content: str) -> dict:
    """Parse a SKILL.md file into structured metadata and sections."""
    result = {
        "sections": [],
        "section_headings": [],
        "frontmatter": {},
        "has_description_trigger": False,
        "trigger_keywords": [],
        "sop_pattern": None,
        "line_count": 0,
        "has_nonempty_instructions": False,
    }

    lines = content.split("\n")
    result["line_count"] = len(lines)

    # Parse frontmatter
    if content.startswith("---"):
        end = content.find("---", 3)
        if end > 0:
            fm_text = content[3:end]
            fm_lines = fm_text.strip().split("\n")
            i = 0
            while i < len(fm_lines):
                line = fm_lines[i]
                if ":" not in line:
                    i += 1
                    continue
                key, _, val = line.partition(":")
                key = key.strip()
                val = val.strip()
                if val in {"|", ">", "|-", ">-", "|+", ">+"}:
                    block = []
                    i += 1
                    while i < len(fm_lines) and (
                        not fm_lines[i].strip() or fm_lines[i][0].isspace()
                    ):
                        block.append(fm_lines[i].strip())
                        i += 1
                    result["frontmatter"][key] = " ".join(
                        part for part in block if part
                    )
                    continue
                result["frontmatter"][key] = val.strip("\"'")
                i += 1
            content_body = content[end + 3:]
        else:
            content_body = content
    else:
        content_body = content

    result["has_nonempty_instructions"] = bool(content_body.strip())

    # Detect description trigger patterns such as "Use when...".
    desc = result["frontmatter"].get("description", "")
    if desc:
        result["has_description_trigger"] = bool(
            re.search(r"Use\s+(when|this|for)\b", desc, re.IGNORECASE)
        )
        # Extract trigger keywords from description
        trigger_match = re.findall(r"`([^`]+)`", desc)
        result["trigger_keywords"] = trigger_match[:10]

    # Parse sections
    current_section = None
    current_content = []
    for line in content_body.split("\n"):
        if line.startswith("## "):
            if current_section:
                result["sections"].append({
                    "heading": current_section,
                    "content": "\n".join(current_content).strip(),
                    "line_count": len(current_content),
                })
            current_section = line[3:].strip()
            result["section_headings"].append(current_section)
            current_content = []
        elif current_section:
            current_content.append(line)
    # Don't forget last section
    if current_section:
        result["sections"].append({
            "heading": current_section,
            "content": "\n".join(current_content).strip(),
            "line_count": len(current_content),
        })

    # Detect SOP pattern
    result["sop_pattern"] = detect_sop_pattern(result)

    # Detect operation types
    result["operation_types"] = detect_operation_types(content_body)

    return result


def is_corpus_eligible(parsed: dict, skill_meta: dict) -> bool:
    """Apply the paper's integrity filter before grammar statistics are computed."""
    frontmatter = parsed.get("frontmatter", {})
    has_metadata = bool(frontmatter.get("name") and frontmatter.get("description"))
    has_source_id = bool(
        skill_meta.get("key")
        and skill_meta.get("owner")
        and skill_meta.get("repo")
        and skill_meta.get("name")
    )
    return bool(has_metadata and parsed.get("has_nonempty_instructions") and has_source_id)


def detect_sop_pattern(parsed: dict) -> str | None:
    """Detect which SOP template the skill follows."""
    headings = [h.lower() for h in parsed["section_headings"]]
    heading_text = " ".join(headings)

    # Check all section content for patterns
    all_text = " ".join(s.get("content", "") for s in parsed["sections"])

    # chain-of-steps: numbered steps
    step_count = len(re.findall(r"(?:^|\n)\s*(?:\d+\.\s|Step\s+\d)", all_text))
    if step_count >= 3:
        return "chain-of-steps"

    # model-card-driven: references to external model cards
    if any(h for h in headings if "model" in h and ("card" in h or "operation" in h)):
        return "model-card-driven"
    if re.search(r"references?/sop_models?", all_text, re.IGNORECASE):
        return "model-card-driven"

    # decision-tree: if-then branching
    if_count = len(re.findall(r"(?:^|\n)\s*(?:If|When|if)\s+.*?(?:→|->|then|go to)", all_text))
    if if_count >= 3:
        return "decision-tree"

    # template-fill: collect → validate → fill → output
    if re.search(r"template|fill|collect.*validate|form", all_text, re.IGNORECASE):
        return "template-fill"

    # Default for skills with clear instructions
    if "instructions" in heading_text or "steps" in heading_text or "workflow" in heading_text:
        return "chain-of-steps"

    return "reference"  # informational / lookup style


def detect_operation_types(text: str) -> list[str]:
    """Detect what operation types the skill performs."""
    ops = []
    patterns = {
        "extract": [r"\bextract\b", r"\bparse\b", r"\bscrape\b"],
        "diagnose": [r"\bdiagnos\b", r"\bdebug\b", r"\baudit\b", r"\bcheck\b", r"\binspect\b"],
        "transform": [r"\btransform\b", r"\bconvert\b", r"\bmigrate\b", r"\brefactor\b"],
        "validate": [r"\bvalid\b", r"\bverify\b", r"\blint\b", r"\btest\b", r"\bensure\b"],
        "generate": [r"\bgenerat\b", r"\bcreat\b", r"\bbuild\b", r"\bscaffold\b"],
        "compare": [r"\bcompar\b", r"\bdiff\b", r"\bversus\b", r"\breview\b"],
    }
    text_lower = text.lower()
    for op_type, pats in patterns.items():
        if any(re.search(p, text_lower) for p in pats):
            ops.append(op_type)
    return ops if ops else ["reference"]


def score_skill_quality(parsed: dict) -> tuple[int, list[str], list[str]]:
    """Score a SKILL.md on quality dimensions. Returns (score, strengths, weaknesses).

    Max score: 13. Top 60% cutoff is typically around 5-6.
    """
    score = 0
    strengths = []
    weaknesses = []

    fm = parsed.get("frontmatter", {})
    headings = [h.lower() for h in parsed.get("section_headings", [])]
    all_text = " ".join(s.get("content", "") for s in parsed.get("sections", []))
    desc = fm.get("description", "")

    # --- Structure quality ---
    if fm.get("name"):
        score += 1
        strengths.append("has_frontmatter_name")
    else:
        weaknesses.append("missing_frontmatter_name")

    if desc:
        score += 1
        strengths.append("has_description")
    else:
        weaknesses.append("missing_description")

    if re.search(r"Use\s+(when|this|for)\b", desc, re.IGNORECASE):
        score += 2
        strengths.append("description_has_trigger")
    elif desc and len(desc) < 30:
        weaknesses.append("description_too_vague")

    if len(desc) > 80:
        score += 1
        strengths.append("description_specific")

    if len(parsed.get("section_headings", [])) >= 3:
        score += 1
        strengths.append("has_multiple_sections")
    else:
        weaknesses.append("too_few_sections")

    has_boundary = any(
        kw in h for h in headings
        for kw in ["boundary", "limitation", "cannot"]
    ) or any(
        kw in s.get("content", "").lower()
        for s in parsed.get("sections", [])
        for kw in ["cannot", "don't use", "limitation"]
    )
    if has_boundary:
        score += 2
        strengths.append("has_boundary_section")

    # --- Content quality ---
    step_patterns = [r"(?:^|\n)\s*\d+\.\s", r"(?:^|\n)\s*Step\s+\d", r"(?:^|\n)\s*[-*]\s"]
    step_count = sum(len(re.findall(p, all_text)) for p in step_patterns)
    if step_count >= 5:
        score += 2
        strengths.append("has_concrete_steps")
    elif step_count >= 2:
        score += 1
        strengths.append("has_some_steps")
    else:
        weaknesses.append("no_concrete_steps")

    has_examples = any("example" in h or "demo" in h for h in headings)
    if has_examples:
        score += 1
        strengths.append("has_examples_section")

    lc = parsed.get("line_count", 0)
    if 80 <= lc <= 400:
        score += 1
        strengths.append("line_count_sweet_spot")
    elif lc < 30:
        score -= 2
        weaknesses.append("too_thin")
    elif lc > 1000:
        weaknesses.append("too_long")

    has_refs = any("reference" in h or "related" in h for h in headings)
    if has_refs:
        score += 1
        strengths.append("has_references_section")

    return max(0, score), strengths, weaknesses


def extract_trigger_pattern(parsed: dict) -> str:
    """Categorize the skill's trigger mechanism."""
    desc = parsed["frontmatter"].get("description", "").lower()
    headings = [h.lower() for h in parsed["section_headings"]]

    has_keywords = any(
        kw in desc for kw in [
            "use when", "use this", "use for", "when you", "when the",
        ]
    )
    has_context = any(
        kw in desc for kw in [
            "project", "directory", "file", "repo", "codebase", "working",
        ]
    )
    has_explicit = "activation" in " ".join(headings)

    if has_keywords and has_context:
        return "hybrid"
    elif has_keywords:
        return "keyword-match"
    elif has_context:
        return "context-match"
    elif has_explicit:
        return "explicit-call"
    else:
        return "keyword-match"  # default — description acts as keyword match


def extract_boundary_pattern(parsed: dict) -> list[str]:
    """Extract boundary patterns from the skill."""
    boundaries = []
    boundary_section = None
    for s in parsed["sections"]:
        if any(kw in s["heading"].lower() for kw in ["boundary", "limitation"]):
            boundary_section = s["content"]
            break

    if not boundary_section:
        return boundaries

    text = boundary_section.lower()
    if any(kw in text for kw in ["source", "based on", "official"]):
        boundaries.append("source-bound")
    if any(kw in text for kw in ["version", "as of"]):
        boundaries.append("version-bound")
    if any(kw in text for kw in ["cannot", "not able", "don't", "can not"]):
        boundaries.append("capability-bound")
    if any(kw in text for kw in ["applicable", "scope"]):
        boundaries.append("scope-bound")
    if any(kw in text for kw in ["legal", "advice", "compliance", "disclaimer"]):
        boundaries.append("legal-bound")
    return boundaries if boundaries else ["capability-bound"]


def detect_skill_mode(parsed: dict) -> str:
    """Detect whether a skill is persona or tool mode.

    Persona skills are character-based role-playing skills, such as skills based
    on Jensen Huang or Zhang Yiming. They have unique sections such as
    Role-Playing Rules, How I See the World, and Things I Would Never Say.
    Tool skills may share some section names, but never have role-playing rules.
    """
    headings = [h.lower() for h in parsed.get("section_headings", [])]
    all_text = " ".join(s.get("content", "") for s in parsed.get("sections", []))
    full = " ".join(headings) + " " + all_text
    full_lower = full.lower()

    # Strong persona signals — these ONLY appear in character persona skills
    persona_strong = ["role-playing rules", "how i see the world", "things i would never say"]
    if any(s in full for s in persona_strong):
        return "persona"

    # Medium persona: need 2+ of these together
    persona_medium = ["identity", "how i speak", "signature phrase", "decision heuristics", "runtime protocol"]
    persona_medium_hits = sum(1 for s in persona_medium if s in full)
    if persona_medium_hits >= 3:
        return "persona"

    # Strong tool signals
    tool_strong = ["activation rules", "agentic protocol", "operation models"]
    if any(s in full_lower for s in tool_strong):
        return "tool"

    # Default: tool mode (skills.sh corpus is overwhelmingly tool skills)
    return "tool"


def build_index():
    """Main entry point."""
    if not MANIFEST_PATH.exists():
        print("No manifest found. Run build_corpus.py first.")
        return

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    skills = [s for s in manifest["skills"] if s["status"] in ("ok", "cached")]

    if not skills:
        print("No fetched skills in manifest. Run build_corpus.py first.")
        return

    print(f"Indexing {len(skills)} fetched skills...")

    # Global stats
    grammar_stats = {
        "total_skills_fetched": len(skills),
        "total_skills_indexed": 0,
        "excluded_by_integrity_filter": 0,
        "skill_mode": Counter(),
        "trigger_patterns": Counter(),
        "sop_patterns": Counter(),
        "operation_types": Counter(),
        "boundary_patterns": Counter(),
        "section_headings": Counter(),
        "line_count_distribution": {"<100": 0, "100-300": 0, "300-800": 0, "800+": 0},
        "common_missing_sections": Counter(),
        "description_has_trigger": 0,
    }

    # Component index: keyed by facet → list of component refs
    index = {
        "by_domain": {},
        "by_skill_mode": {},
        "by_trigger_pattern": {},
        "by_sop_pattern": {},
        "by_operation_type": {},
        "by_boundary_pattern": {},
        "components": [],
    }

    all_section_headings = Counter()
    skills_with_description_trigger = 0

    for i, skill_meta in enumerate(skills):
        skill_path = CORPUS_DIR / f"{skill_meta['key']}.md"
        if not skill_path.exists():
            continue

        try:
            content = skill_path.read_text(encoding="utf-8")
        except Exception:
            continue

        parsed = parse_skill_md(content)

        if not is_corpus_eligible(parsed, skill_meta):
            grammar_stats["excluded_by_integrity_filter"] += 1
            continue
        grammar_stats["total_skills_indexed"] += 1

        # Update global stats
        trigger = extract_trigger_pattern(parsed)
        grammar_stats["trigger_patterns"][trigger] += 1

        sop = parsed["sop_pattern"] or "unknown"
        grammar_stats["sop_patterns"][sop] += 1

        for op in parsed["operation_types"]:
            grammar_stats["operation_types"][op] += 1

        for bp in extract_boundary_pattern(parsed):
            grammar_stats["boundary_patterns"][bp] += 1

        for h in parsed["section_headings"]:
            all_section_headings[h] += 1

        lc = parsed["line_count"]
        if lc < 100:
            grammar_stats["line_count_distribution"]["<100"] += 1
        elif lc < 300:
            grammar_stats["line_count_distribution"]["100-300"] += 1
        elif lc < 800:
            grammar_stats["line_count_distribution"]["300-800"] += 1
        else:
            grammar_stats["line_count_distribution"]["800+"] += 1

        if parsed["has_description_trigger"]:
            skills_with_description_trigger += 1

        # Quality scoring + skill mode
        quality_score, strengths, weaknesses = score_skill_quality(parsed)
        skill_mode = detect_skill_mode(parsed)
        grammar_stats["skill_mode"][skill_mode] += 1

        # Build component entries
        comp = {
            "skill_key": skill_meta["key"],
            "owner": skill_meta["owner"],
            "repo": skill_meta["repo"],
            "name": skill_meta["name"],
            "skill_mode": skill_mode,
            "trigger_pattern": trigger,
            "sop_pattern": sop,
            "operation_types": parsed["operation_types"],
            "boundary_patterns": extract_boundary_pattern(parsed),
            "section_headings": parsed["section_headings"],
            "line_count": parsed["line_count"],
            "has_frontmatter_description": bool(parsed["frontmatter"].get("description")),
            "has_frontmatter_name": bool(parsed["frontmatter"].get("name")),
            "quality_score": quality_score,
            "quality_strengths": strengths,
            "quality_weaknesses": weaknesses,
        }
        index["components"].append(comp)

        # Index by facets (all skills)
        index["by_skill_mode"].setdefault(skill_mode, []).append(comp["skill_key"])
        for domain_tag in (skill_meta.get("topics") or []):
            domain_key = f"topic_{domain_tag}"
            index["by_domain"].setdefault(domain_key, []).append(comp["skill_key"])
        index["by_trigger_pattern"].setdefault(trigger, []).append(comp["skill_key"])
        index["by_sop_pattern"].setdefault(sop, []).append(comp["skill_key"])
        for op in parsed["operation_types"]:
            index["by_operation_type"].setdefault(op, []).append(comp["skill_key"])
        for bp in extract_boundary_pattern(parsed):
            index["by_boundary_pattern"].setdefault(bp, []).append(comp["skill_key"])

        if (i + 1) % 100 == 0:
            print(f"  [{i+1}/{len(skills)}] indexed")

    # Finalize all-skill stats
    grammar_stats["description_has_trigger"] = skills_with_description_trigger
    grammar_stats["top_section_headings"] = all_section_headings.most_common(30)
    grammar_stats["section_headings"] = dict(all_section_headings.most_common(50))

    # --- Quality filtering: top 60% ---
    components = index["components"]
    components.sort(key=lambda c: c["quality_score"], reverse=True)
    cutoff = max(1, int(len(components) * 0.6))
    top_components = components[:cutoff]
    top_keys = {c["skill_key"] for c in top_components}

    quality_threshold = top_components[-1]["quality_score"]
    print(f"\n  Quality cutoff (top 60%): score >= {quality_threshold}")
    print(f"  Top skills: {len(top_components)}, Excluded: {len(components) - cutoff}")

    # Quality-filtered stats
    qual_stats = {
        "filter": f"top_60pct_quality_score_>={quality_threshold}",
        "skills_included": len(top_components),
        "skills_excluded": len(components) - cutoff,
        "quality_score_distribution": {},
        "skill_mode": Counter(),
        "trigger_patterns": Counter(),
        "sop_patterns": Counter(),
        "operation_types": Counter(),
        "boundary_patterns": Counter(),
        "section_headings": Counter(),
        "line_count_distribution": {"<100": 0, "100-300": 0, "300-800": 0, "800+": 0},
        "description_has_trigger": 0,
    }

    # Cross-dimension correlations
    correlations = Counter()
    q_section_headings = Counter()

    for c in top_components:
        score = c["quality_score"]
        bucket = f"{score}"
        qual_stats["quality_score_distribution"][bucket] = \
            qual_stats["quality_score_distribution"].get(bucket, 0) + 1

        qual_stats["skill_mode"][c["skill_mode"]] += 1
        qual_stats["trigger_patterns"][c["trigger_pattern"]] += 1
        qual_stats["sop_patterns"][c["sop_pattern"]] += 1
        for op in c["operation_types"]:
            qual_stats["operation_types"][op] += 1
        for bp in c["boundary_patterns"]:
            qual_stats["boundary_patterns"][bp] += 1
        for h in c["section_headings"]:
            q_section_headings[h] += 1

        lc = c["line_count"]
        if lc < 100:
            qual_stats["line_count_distribution"]["<100"] += 1
        elif lc < 300:
            qual_stats["line_count_distribution"]["100-300"] += 1
        elif lc < 800:
            qual_stats["line_count_distribution"]["300-800"] += 1
        else:
            qual_stats["line_count_distribution"]["800+"] += 1

        if c["has_frontmatter_description"] and c["has_frontmatter_name"]:
            qual_stats["description_has_trigger"] += 1

        # Cross-dimension: record co-occurrence patterns
        trigger_sop = f"trigger={c['trigger_pattern']} + sop={c['sop_pattern']}"
        correlations[trigger_sop] += 1
        for op in c["operation_types"]:
            correlations[f"sop={c['sop_pattern']} + op={op}"] += 1

    qual_stats["top_section_headings"] = q_section_headings.most_common(30)
    qual_stats["top_correlations"] = correlations.most_common(25)

    # --- Quality-weighted differences ---
    differences = {
        "trigger_shift": {},
        "sop_shift": {},
        "line_count_shift": {},
    }
    all_total = len(components)
    qual_total = len(top_components)
    for k in set(list(grammar_stats["trigger_patterns"].keys()) +
                 list(qual_stats["trigger_patterns"].keys())):
        all_pct = grammar_stats["trigger_patterns"].get(k, 0) / all_total * 100
        qual_pct = qual_stats["trigger_patterns"].get(k, 0) / qual_total * 100
        if abs(all_pct - qual_pct) > 3:  # meaningful shift
            differences["trigger_shift"][k] = f"{all_pct:.0f}%→{qual_pct:.0f}%"

    for k in set(list(grammar_stats["sop_patterns"].keys()) +
                 list(qual_stats["sop_patterns"].keys())):
        all_pct = grammar_stats["sop_patterns"].get(k, 0) / all_total * 100
        qual_pct = qual_stats["sop_patterns"].get(k, 0) / qual_total * 100
        if abs(all_pct - qual_pct) > 3:
            differences["sop_shift"][k] = f"{all_pct:.0f}%→{qual_pct:.0f}%"

    for k in ["<100", "100-300", "300-800", "800+"]:
        all_pct = grammar_stats["line_count_distribution"][k] / all_total * 100
        qual_pct = qual_stats["line_count_distribution"][k] / qual_total * 100
        if abs(all_pct - qual_pct) > 3:
            differences["line_count_shift"][k] = f"{all_pct:.0f}%→{qual_pct:.0f}%"

    qual_stats["quality_vs_all_skill_differences"] = differences

    # Add quality index: which skills are the best exemplars?
    index["by_quality"] = {
        "top_10": [c["skill_key"] for c in components[:10]],
        "top_60pct": list(top_keys),
        "quality_scores": {c["skill_key"]: c["quality_score"] for c in components},
    }
    index["quality_summary"] = {
        "total_skills": len(components),
        "score_range": [components[-1]["quality_score"], components[0]["quality_score"]],
        "median_score": components[len(components)//2]["quality_score"],
        "top_60pct_cutoff_score": quality_threshold,
    }

    # Write outputs
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2))

    # Combined stats
    full_stats = {
        "all_skills": grammar_stats,
        "top_60pct_quality": qual_stats,
    }
    STATS_PATH.write_text(json.dumps(full_stats, ensure_ascii=False, indent=2))

    print(f"\nComponent index written to {INDEX_PATH}")
    print(f"Grammar stats written to {STATS_PATH}")
    print(f"\nKey findings (all skills):")
    print(f"  Trigger patterns: {dict(grammar_stats['trigger_patterns'].most_common())}")
    print(f"  SOP patterns: {dict(grammar_stats['sop_patterns'].most_common())}")
    print(f"  Line count dist: {grammar_stats['line_count_distribution']}")
    print(
        "  Skills with description trigger: "
        f"{skills_with_description_trigger}/{grammar_stats['total_skills_indexed']}"
    )
    print(f"\nQuality-filtered (top 60%, score>={quality_threshold}):")
    print(f"  Trigger patterns: {dict(qual_stats['trigger_patterns'].most_common())}")
    print(f"  SOP patterns: {dict(qual_stats['sop_patterns'].most_common())}")
    print(f"  Significant shifts from all-skill: {differences}")
    print(f"  Top correlations: {correlations.most_common(5)}")


if __name__ == "__main__":
    build_index()
