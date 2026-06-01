#!/usr/bin/env python3
"""
Build LEAP skill corpus from skills.sh sitemap.

Fetches SKILL.md files from GitHub raw for a curated sample of the 20,000
skills registered on skills.sh. Uses multi-pattern URL guessing with
fallback strategies.

Usage:
    python3 scripts/build_corpus.py                    # sample mode (default: 500)
    python3 scripts/build_corpus.py --sample 1000      # custom sample size
    python3 scripts/build_corpus.py --official-only    # official repos only
    python3 scripts/build_corpus.py --all              # attempt all 20k (slow!)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "corpus" / "skills"
MANIFEST_PATH = ROOT / "corpus" / "manifest.json"
SITEMAP_URLS = [
    "https://skills.sh/sitemap-skills-1.xml",
    "https://skills.sh/sitemap-skills-2.xml",
]
REQUEST_TIMEOUT = 15

# Repos known to produce high-quality, well-structured skills.
# Prioritized for full inclusion.
OFFICIAL_REPOS = {
    "anthropics/skills",
    "vercel-labs/skills",
    "vercel-labs/agent-skills",
    "vercel-labs/next-skills",
    "microsoft/azure-skills",
    "obra/superpowers",
    "supabase/agent-skills",
    "remotion-dev/skills",
    "larksuite/cli",
    "shadcn/ui",
    "mattpocock/skills",
    "coreyhaines31/marketingskills",
}

# Topic keywords for stratified sampling.
# Each keyword group ensures domain diversity.
TOPIC_GROUPS = [
    ["security", "vulnerability", "audit", "owasp", "compliance"],
    ["testing", "test", "tdd", "playwright", "jest", "pytest"],
    ["design", "ui", "ux", "css", "tailwind", "frontend"],
    ["database", "sql", "postgres", "mongodb", "redis"],
    ["devops", "docker", "kubernetes", "ci", "deploy", "terraform"],
    ["data", "analysis", "pandas", "visualization", "analytics"],
    ["api", "rest", "graphql", "openapi"],
    ["mobile", "react-native", "ios", "android", "flutter"],
    ["ai", "llm", "prompt", "agent", "machine-learning"],
    ["documentation", "docs", "readme", "writing"],
    ["git", "github", "pr", "branch", "commit"],
    ["performance", "optimization", "profiling", "benchmark"],
]

RAW_URL_PATTERNS = [
    "https://raw.githubusercontent.com/{owner}/{repo}/main/skills/{name}/SKILL.md",
    "https://raw.githubusercontent.com/{owner}/{repo}/main/{name}/SKILL.md",
    "https://raw.githubusercontent.com/{owner}/{repo}/master/skills/{name}/SKILL.md",
    "https://raw.githubusercontent.com/{owner}/{repo}/master/{name}/SKILL.md",
]


def parse_sitemap(url: str) -> list[dict]:
    """Parse a skills.sh sitemap XML into a list of skill descriptors."""
    skills = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LEAP/0.4.0"})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            tree = ET.parse(resp)
        for url_elem in tree.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
            loc = url_elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
            lastmod = url_elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
            if loc is not None and loc.text:
                path = loc.text.split("skills.sh/", 1)[-1].strip("/")  # handle www.skills.sh
                parts = path.split("/")
                if len(parts) >= 3:
                    skills.append({
                        "owner": parts[0],
                        "repo": parts[1],
                        "name": parts[2],
                        "full_path": path,
                        "lastmod": lastmod.text if lastmod is not None else None,
                    })
    except Exception as e:
        print(f"  [WARN] Failed to parse sitemap {url}: {e}")
    return skills


def fetch_skill_md(owner: str, repo: str, name: str) -> tuple[str | None, str | None]:
    """Try to fetch a SKILL.md file using multiple URL patterns.
    Returns (content, successful_url) or (None, None).
    """
    for pattern in RAW_URL_PATTERNS:
        url = pattern.format(owner=owner, repo=repo, name=name)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "LEAP/0.4.0"})
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                if resp.status == 200:
                    content = resp.read().decode("utf-8", errors="replace")
                    if "---" in content and len(content) > 100:
                        return content, url
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
        except Exception:
            continue
    return None, None


def match_topics(name: str, repo: str) -> list[int]:
    """Return indices of topic groups this skill matches."""
    text = (name + " " + repo).lower()
    return [i for i, keywords in enumerate(TOPIC_GROUPS)
            if any(kw in text for kw in keywords)]


def build_corpus(sample_size: int = 500, official_only: bool = False,
                 fetch_all: bool = False) -> dict:
    """Main entry point. Returns manifest dict."""
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    # --- 1. Parse sitemaps ---
    print("Fetching sitemaps...")
    all_skills = []
    for url in SITEMAP_URLS:
        skills = parse_sitemap(url)
        all_skills.extend(skills)
        print(f"  {url} → {len(skills)} skills")
    print(f"  Total: {len(all_skills)} skills")

    # --- 2. Select skills to fetch ---
    official = [s for s in all_skills if f"{s['owner']}/{s['repo']}" in OFFICIAL_REPOS]
    rest = [s for s in all_skills if f"{s['owner']}/{s['repo']}" not in OFFICIAL_REPOS]

    if official_only:
        selected = official
    elif fetch_all:
        selected = all_skills
    else:
        # Stratified: all official + topic-diverse sample from rest
        selected = list(official)
        # Group rest by topic match
        topic_buckets = {i: [] for i in range(len(TOPIC_GROUPS))}
        unmatched = []
        for s in rest:
            matches = match_topics(s["name"], s["repo"])
            if matches:
                for m in matches:
                    topic_buckets[m].append(s)
            else:
                unmatched.append(s)
        # Sample from each bucket
        per_bucket = max(1, (sample_size - len(official)) // (len(TOPIC_GROUPS) + 1))
        for bucket in topic_buckets.values():
            selected.extend(bucket[:per_bucket])
        # Random sample from unmatched to fill remaining
        remaining = sample_size - len(selected)
        if remaining > 0 and unmatched:
            import random
            random.shuffle(unmatched)
            selected.extend(unmatched[:remaining])

    # Deduplicate
    seen = set()
    unique = []
    for s in selected:
        key = f"{s['owner']}/{s['repo']}/{s['name']}"
        if key not in seen:
            seen.add(key)
            unique.append(s)
    selected = unique[:sample_size] if not (official_only or fetch_all) else unique

    print(f"\nSelected {len(selected)} skills to fetch "
          f"(official={len(official)}, fetch_all={fetch_all})")

    # --- 3. Fetch SKILL.md files (parallel) ---
    manifest = {
        "total_selected": len(selected),
        "fetched": 0,
        "failed": 0,
        "skills": [],
        "repo_patterns": {},
    }

    # Separate cached from to-fetch
    to_fetch = []
    for skill in selected:
        key = f"{skill['owner']}~{skill['repo']}~{skill['name']}"
        out_path = CORPUS_DIR / f"{key}.md"
        if out_path.exists():
            manifest["skills"].append({
                "key": key, "owner": skill["owner"], "repo": skill["repo"],
                "name": skill["name"], "status": "cached",
                "lastmod": skill["lastmod"],
                "topics": match_topics(skill["name"], skill["repo"]),
            })
            manifest["fetched"] += 1
        else:
            to_fetch.append((skill, key, out_path))

    print(f"  Cached: {manifest['fetched']}, To fetch: {len(to_fetch)}")
    print(f"  Downloading with {min(20, len(to_fetch))} parallel workers...")

    # Parallel fetch
    fetched_count = manifest["fetched"]
    failed_count = 0
    completed = 0

    def _fetch_one(skill, key, out_path):
        content, url = fetch_skill_md(skill["owner"], skill["repo"], skill["name"])
        return skill, key, out_path, content, url

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(_fetch_one, s, k, p): (s, k, p)
                   for s, k, p in to_fetch}
        for future in as_completed(futures):
            completed += 1
            skill, key, out_path, content, url = future.result()

            if completed % 50 == 0:
                print(f"  [{completed}/{len(to_fetch)}] "
                      f"ok={fetched_count - manifest.get('fetched', 0) + manifest['fetched']} "
                      f"fail={failed_count}")

            if content:
                out_path.write_text(content, encoding="utf-8")
                repo_key = f"{skill['owner']}/{skill['repo']}"
                if repo_key not in manifest["repo_patterns"]:
                    manifest["repo_patterns"][repo_key] = url
                manifest["skills"].append({
                    "key": key, "owner": skill["owner"], "repo": skill["repo"],
                    "name": skill["name"], "status": "ok",
                    "url": url, "lastmod": skill["lastmod"],
                    "topics": match_topics(skill["name"], skill["repo"]),
                })
                fetched_count += 1
            else:
                manifest["skills"].append({
                    "key": key, "owner": skill["owner"], "repo": skill["repo"],
                    "name": skill["name"], "status": "failed",
                    "lastmod": skill["lastmod"],
                    "topics": match_topics(skill["name"], skill["repo"]),
                })
                failed_count += 1

    manifest["fetched"] = fetched_count
    manifest["failed"] = failed_count

    print(f"\nDone. Fetched: {manifest['fetched']}, Failed: {manifest['failed']}")
    print(f"Success rate: {manifest['fetched']/max(1,len(selected))*100:.1f}%")

    # --- 4. Write manifest ---
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"Manifest written to {MANIFEST_PATH}")

    return manifest


def main():
    parser = argparse.ArgumentParser(description="Build LEAP skill corpus from skills.sh")
    parser.add_argument("--sample", type=int, default=500,
                        help="Number of skills to sample (default: 500)")
    parser.add_argument("--official-only", action="store_true",
                        help="Only fetch from official/verified repos")
    parser.add_argument("--all", action="store_true",
                        help="Fetch ALL 20k skills (slow, use with care)")
    args = parser.parse_args()
    build_corpus(sample_size=args.sample, official_only=args.official_only,
                 fetch_all=args.all)


if __name__ == "__main__":
    main()
