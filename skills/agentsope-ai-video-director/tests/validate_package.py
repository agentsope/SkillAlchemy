#!/usr/bin/env python3
"""Validate authored runtime structure, reachability, traceability and optional hashes."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

FILES = ['SKILL.md', 'skill.json', 'README.md', 'LICENSE',
         'references/sources.md', 'references/prompt-patterns.md', 'references/director-playbook.md',
         'references/video-types.md', 'references/engine-adapters.md', 'references/quality-rubric.md',
         'references/case-studies.md', 'references/sop_models.md', 'references/research_notes.md', 'references/provenance.json',
         'examples/sentence-to-director-plan.md', 'examples/hyperframes-prompt.md', 'examples/remotion-prompt.md',
         'examples/product-launch.md', 'examples/data-explainer.md', 'examples/narrated-docs.md',
         'tests/sentence-inputs.json', 'tests/engine-routing.json', 'tests/missing-and-errors.json',
         'tests/quality-checklist.md', 'tests/manual-review.md', 'tests/validate_package.py', 'tests/validate_outputs.py']
HEADINGS = ['Activation Rules', 'Agentic Protocol', 'Core Operation Models', 'Output Style', 'Output Modes', 'Boundary Rules', 'References']
FORBIDDEN_PARTS = {'node_modules', '.git', 'tooling', 'research-cache', 'exemplars', 'npm-cache', '__pycache__'}


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root, manifest=None):
    errors = []
    def need(condition, message):
        if not condition:
            errors.append(message)
    root = root.resolve()
    for name in FILES:
        path = root / name
        need(path.is_file() and path.stat().st_size > 0, f'Missing/nonempty required runtime file: {name}')
        need(path.resolve().is_relative_to(root), f'Runtime symlink escapes package: {name}')
    skill_path = root / 'SKILL.md'
    if not skill_path.is_file():
        return errors
    text = skill_path.read_text(encoding='utf-8')
    lines = text.splitlines()
    need(100 <= len(lines) <= 300, 'SKILL.md must have 100–300 lines')
    need(len(re.findall(r'\S+', text)) < 5000, 'SKILL.md exceeds authored conservative 5000 whitespace-word budget; token count requires separate tooling')
    match = re.match(r'\A---\s*\n(.*?)\n---\s*\n', text, re.S)
    need(bool(match), 'SKILL.md frontmatter missing')
    if match:
        front = match.group(1)
        name = re.search(r'^name:\s*(\S+)', front, re.M)
        need(bool(name) and bool(re.fullmatch(r'[a-z0-9-]{1,64}', name.group(1))), 'frontmatter name invalid')
        desc = re.search(r'^description:\s*(.*)', front, re.M)
        need(bool(desc), 'description missing')
        if desc:
            description = front[desc.start():].split('\n', 1)[-1] if desc.group(1).strip() in {'|', '>-', '>', '|-'} else desc.group(1)
            need(1 <= len(description.strip()) <= 1024, 'frontmatter description must be 1–1024 chars')
            need(bool(re.search(r'use when|when|用于|当', description, re.I)), 'description must include functional trigger')
    need(re.findall(r'^## (.+)$', text, re.M) == HEADINGS, 'SKILL.md exact seven tool-mode sections required')
    adjacency = {name: set() for name in FILES}
    for name in FILES:
        path = root / name
        if path.suffix != '.md' or not path.is_file():
            continue
        body = path.read_text(encoding='utf-8')
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', body):
            target = target.split(' "', 1)[0].strip().strip('<>')
            if re.match(r'^(?:https?://|mailto:|#)', target):
                continue
            target = target.split('#', 1)[0]
            resolved = (path.parent / target).resolve()
            need(resolved.is_relative_to(root), f'{name}: link escapes runtime: {target}')
            if resolved.is_relative_to(root):
                rel = resolved.relative_to(root).as_posix()
                need(resolved.is_file() and rel in FILES, f'{name}: runtime link missing/not in manifest: {target}')
                if rel in FILES:
                    adjacency[name].add(rel)
    reached, queue = set(), ['SKILL.md']
    while queue:
        name = queue.pop()
        if name not in reached:
            reached.add(name)
            queue.extend(adjacency.get(name, set()))
    need(set(FILES) <= reached, 'Every runtime file must be reachable from SKILL.md: ' + ', '.join(sorted(set(FILES) - reached)))
    provenance_path = root / 'references/provenance.json'
    if provenance_path.is_file():
        try:
            provenance = load(provenance_path)
            candidates = provenance.get('candidates', [])
            need(isinstance(candidates, list) and len(candidates) == 40, 'provenance must retain all 40 admitted candidates')
            ids = [c.get('candidate_id') for c in candidates]
            need(set(ids) == {f'P{i:02}' for i in range(1, 41)} and len(set(ids)) == 40, 'candidate IDs P01–P40 required once')
            classifications = [c.get('classification') for c in candidates]
            need(classifications.count('General') == 20 and classifications.count('Scoped') == 20, 'admission partition must remain 20 General/20 Scoped')
            nulls, bindings = 0, 0
            for c in candidates:
                cid = c.get('candidate_id')
                need(bool(c.get('sigma')) and isinstance(c.get('boundaries'), list), f'{cid}: exact scope/boundaries required')
                need(bool(c.get('confidence')) and bool(c.get('verification_state')), f'{cid}: claim/confidence/verification limits missing')
                need(isinstance(c.get('sources'), list) and bool(c['sources']), f'{cid}: sources required')
                for component in ('condition', 'action', 'recovery', 'verification'):
                    comp = c.get(component, {})
                    need(isinstance(comp, dict) and 'content' in comp and isinstance(comp.get('evidence_ids'), list), f'{cid}: {component} structure required')
                    if isinstance(comp, dict) and comp.get('content') is None:
                        nulls += 1
                        need(comp.get('evidence_ids') == [], f'{cid}: unsupported component must retain null/empty evidence')
                    elif isinstance(comp, dict):
                        need(bool(comp.get('evidence_ids')), f'{cid}: populated component requires evidence IDs')
                bindings += len(c.get('engine_profile_bindings', []))
                for binding in c.get('engine_profile_bindings', []):
                    need(all(binding.get(k) for k in ('component', 'content', 'scope', 'actual_observation')), f'{cid}: engine binding scope/observation missing')
            need(nulls == 46, f'Unsupported components must remain exactly 46 nulls (found {nulls})')
            need(bindings == 16, f'All 16 exact admitted engine bindings required (found {bindings})')
            need(set(provenance.get('runtime_manifest', [])) == set(FILES), 'provenance runtime_manifest must be exact 27 files')
            constraint_ids = {c.get('constraint_id') for c in provenance.get('constraints', [])}
            need(constraint_ids == {f'C{i:02}' for i in range(1, 10)}, 'C01–C09 authored constraints required')
            view_path = root / 'intermediate/compile_views.json'
            if view_path.is_file():
                admitted = {c['candidate_id']: c for c in load(view_path)['candidates']}
                for c in candidates:
                    a = admitted.get(c.get('candidate_id'), {})
                    for key in ('condition', 'action', 'recovery', 'verification', 'sigma', 'boundaries', 'confidence', 'verification_state', 'engine_profile_bindings', 'conditional_cases'):
                        need(c.get(key) == a.get(key), f'{c.get("candidate_id")}: exact admitted {key} changed')
            canonical_ids = {x.get('source_id') for x in provenance.get('sources', [])}
            aliases = provenance.get('source_alias_map', {})
            need(isinstance(aliases, dict) and all(value in canonical_ids for value in aliases.values()), 'source aliases must resolve to retained canonical source IDs')
            finding_ids = {f.get('finding_id') for c in candidates for f in c.get('findings', []) if isinstance(f, dict)}
            def resolve_sources(value):
                if isinstance(value, dict):
                    for key, child in value.items():
                        if key.endswith('source_ids') and isinstance(child, list):
                            for source_id in child:
                                need(source_id in canonical_ids or source_id in aliases, f'unresolved source binding: {source_id}')
                        resolve_sources(child)
                elif isinstance(value, list):
                    for child in value:
                        resolve_sources(child)
            for c in candidates:
                for source_id in c.get('sources', []):
                    need(source_id in canonical_ids or source_id in aliases, f'{c.get("candidate_id")}: source ID unresolved {source_id}')
                for component in ('condition', 'action', 'recovery', 'verification'):
                    for finding_id in c.get(component, {}).get('evidence_ids', []):
                        need(finding_id in finding_ids, f'{c.get("candidate_id")}: finding ID unresolved {finding_id}')
                for binding in c.get('engine_profile_bindings', []):
                    for finding_id in binding.get('related_finding_ids', []):
                        need(finding_id in finding_ids, f'{c.get("candidate_id")}: binding finding unresolved {finding_id}')
                resolve_sources(c.get('component_evidence_bindings', {}))
                resolve_sources(c.get('engine_profile_bindings', []))
            for source in provenance.get('sources', []):
                need(bool(source.get('source_id')) and bool(source.get('canonical_url', source.get('url', source.get('exact_source_url')))), 'canonical source ID/URL required')
        except (OSError, ValueError, TypeError, KeyError) as exc:
            need(False, f'provenance malformed: {exc}')
    for name in ('sentence-inputs.json', 'engine-routing.json', 'missing-and-errors.json'):
        path = root / 'tests' / name
        if path.is_file():
            try:
                fixture = load(path)
                cases = fixture.get('cases', [])
                ids = [c.get('test_id') for c in cases]
                need(bool(cases) and len(ids) == len(set(ids)), f'{name}: unique authored case IDs required')
                need(fixture.get('origin'), f'{name}: authored origin missing')
                need(fixture.get('execution_status') == 'not_executed', f'{name}: fixtures describe unexecuted tests; retain actual runs outside runtime')
            except (ValueError, TypeError) as exc:
                need(False, f'{name}: malformed fixture: {exc}')
    metadata = root / 'skill.json'
    if metadata.is_file():
        try:
            meta = load(metadata)
            if 'runtime_manifest' in meta:
                need(set(meta['runtime_manifest']) == set(FILES), 'metadata runtime_manifest must contain exact 27 files')
        except (ValueError, TypeError) as exc:
            need(False, f'skill.json invalid: {exc}')
    if manifest:
        try:
            data = load(manifest)
            entries = data if isinstance(data, list) else data.get('files', data.get('runtime_manifest', []))
            need(isinstance(entries, list) and len(entries) == 27, 'hash manifest requires 27 entries')
            paths = []
            for entry in entries:
                if not isinstance(entry, dict):
                    need(False, 'hash manifest entries must include path/sha256/license/reachability')
                    continue
                name = entry.get('path', entry.get('relative_path'))
                paths.append(name)
                need(name in FILES, f'not an allowed manifest file: {name}')
                if name in FILES and (root / name).is_file():
                    need(entry.get('sha256') == sha(root / name), f'hash mismatch: {name}')
                need(bool(entry.get('license_basis', entry.get('license', entry.get('authored_permitted_license_basis')))), f'manifest license basis missing: {name}')
            need(set(paths) == set(FILES), 'hash manifest exact 27 path set required')
        except (OSError, ValueError, TypeError) as exc:
            need(False, f'manifest invalid: {exc}')
    # When checking the installed runtime rather than local audit root, reject extra files.
    if not (root / 'intermediate').exists():
        actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
        need(actual == set(FILES), 'runtime contains unmanifested/missing files: ' + ', '.join(sorted(actual ^ set(FILES))))
        for p in root.rglob('*'):
            need(not set(p.relative_to(root).parts) & FORBIDDEN_PARTS, f'forbidden runtime material: {p.relative_to(root)}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--manifest', type=Path, help='Optional explicit 27-file hash manifest')
    args = parser.parse_args()
    try:
        errors = validate(args.root, args.manifest)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        errors = [f'Cannot validate package: {exc}']
    print(json.dumps({'status': 'fail' if errors else 'pass', 'errors': errors,
                      'scope': 'stdlib structure/links/exact admission/nulls/bindings/manifest checks; runtime behavior tested separately'}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
