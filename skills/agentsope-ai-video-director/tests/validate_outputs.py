#!/usr/bin/env python3
"""Validate retained actual actor records; never emit or synthesize responses."""
import argparse
import json
import math
import re
import sys
from pathlib import Path

STATUSES = {'pass', 'fail', 'warning', 'not_executed', 'not_applicable', 'unknown'}
STATE_KEYS = ('plan_available', 'code_available', 'static_checked', 'preview_observed',
              'encoded_artifact_available', 'technical_probe_passed', 'sample_frames_reviewed',
              'full_motion_reviewed', 'audio_listened', 'rights_confirmed', 'reproducibility_scope')
DIMENSIONS = ('narrative_clarity', 'visual_consistency', 'pacing', 'animation_quality',
              'text_legibility', 'factual_accuracy', 'audio_quality', 'technical_correctness', 'reproducibility')
VERSIONS = {'hyperframes': '0.8.142', 'remotion_server': '4.0.534',
            'remotion_browser': '4.0.534', 'motion_canvas': '3.17.2'}
REQUIRED_IDS = {'P01', 'P02', 'P03'}


def fixture_registry():
    """Read authored input/behavior contracts; this never supplies actor answers."""
    result = {}
    for name in ('sentence-inputs.json', 'engine-routing.json', 'missing-and-errors.json'):
        fixture = read_json(Path(__file__).resolve().parent / name)
        for case in fixture.get('cases', []):
            test_id = case['test_id']
            if test_id in result:
                raise ValueError(f'duplicate fixture ID: {test_id}')
            result[test_id] = case
    return result


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def numeric(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def check_records(envelope, base):
    contracts = fixture_registry()
    errors = []
    records = envelope.get('records', [])
    def require(condition, message):
        if not condition:
            errors.append(message)
    require(envelope.get('schema_version') == '1.0', 'schema_version must be 1.0')
    require(isinstance(records, list) and bool(records), 'records must be a nonempty list')
    if not isinstance(records, list):
        return errors
    ids = [r.get('test_id') for r in records if isinstance(r, dict)]
    require(len(ids) == len(records) and len(set(ids)) == len(ids), 'record IDs must be unique')
    require(REQUIRED_IDS <= set(ids), 'actual records P01, P02 and P03 are required')
    for record in records:
        if not isinstance(record, dict):
            continue
        tid = record.get('test_id', '<missing>')
        def need(condition, message):
            require(condition, f'{tid}: {message}')
        def file_path(value):
            if not isinstance(value, str) or not value:
                return None
            path = Path(value)
            return path if path.is_absolute() else base / path
        def exists(value):
            path = file_path(value)
            return path is not None and path.is_file() and path.stat().st_size > 0
        contract = contracts.get(tid, {})
        if contract:
            need(record.get('input') == contract.get('input'), 'input must equal the retained authored fixture input')
        for key in ('input', 'actor', 'executed_at', 'response_path'):
            need(isinstance(record.get(key), str) and bool(record[key].strip()), f'{key} required')
        need(bool(re.fullmatch(r'[a-fA-F0-9]{64}', str(record.get('loaded_skill_sha256', '')))), 'loaded_skill_sha256 must identify loaded skill')
        out = record.get('output')
        need(isinstance(out, dict), 'output must be actual structured actor object')
        if not isinstance(out, dict):
            continue
        response = file_path(record.get('response_path'))
        need(response is not None and response.is_file(), 'retained actual response_path must exist')
        if response is not None and response.is_file():
            try:
                need(read_json(response) == out, 'retained response JSON must equal output; no expected-output substitution')
            except (OSError, ValueError) as exc:
                need(False, f'response JSON cannot be read: {exc}')
        plan = out.get('plan', {})
        need(isinstance(plan, dict), 'plan must be an object')
        if not isinstance(plan, dict):
            continue
        for key in ('intent', 'audience', 'main_message', 'platform', 'aspect_ratio', 'audio_intent'):
            need(isinstance(plan.get(key), str) and bool(plan[key]), f'plan.{key} required')
        duration, fps = plan.get('duration_seconds'), plan.get('fps')
        need(numeric(duration) and duration > 0, 'positive finite duration required')
        need(numeric(fps) and fps > 0, 'positive finite fps required')
        width, height = plan.get('width'), plan.get('height')
        need(numeric(width) and width > 0 and numeric(height) and height > 0, 'target dimensions required')
        for key in ('facts', 'unknowns', 'assumptions', 'shots', 'assets'):
            need(isinstance(plan.get(key), list), f'plan.{key} must be a list')
        need(isinstance(plan.get('style'), dict) and bool(plan.get('style')), 'style tokens required')
        for fact in plan.get('facts', []):
            need(isinstance(fact, dict) and fact.get('origin') in {'user', 'sourced', 'derived', 'synthetic'}, 'facts need valid origin')
            if isinstance(fact, dict) and fact.get('origin') == 'sourced':
                need(bool(fact.get('source')), 'sourced fact must have source')
        for assumption in plan.get('assumptions', []):
            need(isinstance(assumption, dict) and bool(assumption.get('field')) and assumption.get('origin') in {'package_default', 'user_assumption'}, 'assumptions must label authored/default origin')
        timeline = plan.get('timeline', {})
        need(isinstance(timeline, dict) and timeline.get('unit') == 'seconds', 'neutral plan timeline uses declared seconds')
        shots = plan.get('shots', [])
        previous = 0.0
        max_end = 0.0
        declared_intervals = timeline.get('intentional_gaps', []) + timeline.get('intentional_overlaps', [])
        need(isinstance(declared_intervals, list), 'declared gap/overlap intervals must be lists')
        if isinstance(shots, list):
            need(bool(shots), 'detailed shots required')
            shot_ids = []
            for shot in shots:
                if not isinstance(shot, dict):
                    need(False, 'shot must be an object')
                    continue
                shot_ids.append(shot.get('id'))
                for key in ('id', 'subject', 'action', 'framing', 'layout', 'copy', 'transition'):
                    need(isinstance(shot.get(key), str) and bool(shot[key]), f'shot {shot.get("id")}: {key} required')
                start, end = shot.get('start_seconds'), shot.get('end_seconds')
                need(numeric(start) and numeric(end) and end > start, 'shot needs positive half-open interval')
                if numeric(start) and numeric(end):
                    if not math.isclose(start, previous, abs_tol=1e-6):
                        lo, hi = min(start, previous), max(start, previous)
                        need(any(isinstance(d, dict) and numeric(d.get('start_seconds')) and numeric(d.get('end_seconds')) and math.isclose(d['start_seconds'], lo, abs_tol=1e-6) and math.isclose(d['end_seconds'], hi, abs_tol=1e-6) and bool(d.get('reason')) for d in declared_intervals), 'unexplained gap/overlap; declare exact interval and reason')
                    previous = end
                    max_end = max(max_end, end)
            need(len(set(shot_ids)) == len(shot_ids), 'shot IDs unique')
        if numeric(duration):
            need(math.isclose(max_end, duration, abs_tol=1e-6), 'shot end must equal requested duration')
            need(numeric(timeline.get('closure_seconds')) and math.isclose(timeline['closure_seconds'], duration, abs_tol=1e-6), 'timeline closure required')
        route = out.get('engine_route', {})
        need(isinstance(route, dict), 'engine_route object required')
        if not isinstance(route, dict):
            route = {}
        profile = route.get('profile')
        need(profile in set(VERSIONS) | {'none', 'canvas_webgl'}, 'recognized isolated engine profile required')
        if profile in VERSIONS:
            need(route.get('version') == VERSIONS[profile], 'exact admitted engine version required')
        need(route.get('decision') in {'selected', 'conditional', 'unavailable'}, 'explicit route decision required')
        need(route.get('eligibility') in {'eligible', 'unknown', 'blocked'}, 'eligibility must remain explicit')
        need(route.get('intended_use') in {'evaluation', 'production'}, 'intended use required')
        need(isinstance(route.get('exporter_available'), bool), 'actual/fixture exporter availability required')
        need(isinstance(route.get('gaps'), list), 'dependency/eligibility gaps required')
        if route.get('decision') == 'selected':
            need(route.get('eligibility') == 'eligible' and route.get('exporter_available') is True, 'selected route requires eligible runnable exporter')
            need(bool(route.get('eligibility_basis')), 'selected eligibility needs subject/use basis')
        if route.get('eligibility') != 'eligible' or route.get('exporter_available') is False:
            need(route.get('decision') != 'selected', 'unknown/blocked/missing exporter cannot be selected')
            need(bool(route.get('gaps')), 'unavailable/conditional route must name concrete gap')
        prompt = out.get('coding_prompt', '')
        need(isinstance(prompt, str) and len(prompt) >= 500, 'detailed coding-agent prompt required (authored minimum 500 characters)')
        if isinstance(prompt, str):
            # These checks detect namespace collisions in the selected implementation, not quoted adapter comparisons.
            if profile == 'hyperframes':
                need(route.get('time_unit') == 'seconds', 'HF timing must use seconds')
                for token in ('0.8.142', 'data-duration', '__timelines', 'paused'):
                    need(token in prompt, f'HF prompt missing {token}')
                need(not any(token in prompt for token in ('useCurrentFrame(', 'renderMediaOnWeb(', 'makeScene2D(')), 'HF prompt imports foreign engine API')
            if profile in {'remotion_server', 'remotion_browser'}:
                need(route.get('time_unit') == 'frames', 'Remotion timing must use frames')
                for token in ('4.0.534', 'durationInFrames', 'useCurrentFrame', 'Sequence'):
                    need(token in prompt, f'Remotion prompt missing {token}')
                need(not any(token in prompt for token in ('data-composition-id=', 'window.__timelines[', 'makeScene2D(')), 'Remotion prompt imports foreign engine API')
                if profile == 'remotion_server':
                    need('renderMediaOnWeb(' not in prompt, 'server prompt uses browser renderer')
                else:
                    need(not re.search(r'(?:\b(?:npx\s+|(?:\./)?node_modules/\.bin/)?remotion\s+render\b|(?:<\s*(?:OffthreadVideo|Html5Video|Html5Audio)\b|\b(?:OffthreadVideo|Html5Video|Html5Audio)\s*\())', prompt), 'browser compositor uses unsupported server/media API')
                for shot in shots if isinstance(shots, list) else []:
                    if isinstance(shot, dict) and numeric(fps) and numeric(shot.get('start_seconds')) and numeric(shot.get('end_seconds')):
                        need(shot.get('start_frame') == round(shot['start_seconds'] * fps) and shot.get('end_frame') == round(shot['end_seconds'] * fps), 'Remotion shot frame conversion required')
            if profile == 'motion_canvas':
                need(route.get('time_unit') == 'seconds', 'Motion Canvas generator timing uses seconds')
                need('3.17.2' in prompt and 'Video (FFmpeg)' in prompt, 'released Motion Canvas editor exporter contract required')
                need(not re.search(r'motion-canvas\s+render|motioncanvas\s+render', prompt, re.I), 'invented Motion Canvas headless CLI')
        audio = plan.get('audio', {})
        need(isinstance(audio, dict) and audio.get('status') in {'none', 'pending', 'ready'}, 'audio status required')
        if not isinstance(audio, dict):
            audio = {}
        need(audio.get('alignment') in {'not_applicable', 'provisional', 'measured', 'approximate'}, 'alignment state required')
        captions = audio.get('captions', [])
        need(isinstance(captions, list), 'captions must be plain-data list')
        for caption in captions if isinstance(captions, list) else []:
            need(isinstance(caption, dict), 'caption object required')
            if isinstance(caption, dict):
                need(isinstance(caption.get('text'), str), 'caption text required; preserve supplied whitespace')
                need(numeric(caption.get('startMs')) and numeric(caption.get('endMs')) and caption['endMs'] > caption['startMs'], 'Caption startMs/endMs use milliseconds')
                need('timestampMs' in caption and (caption['timestampMs'] is None or numeric(caption['timestampMs'])), 'Caption timestampMs numeric/null')
                need('confidence' in caption and (caption['confidence'] is None or numeric(caption['confidence'])), 'Caption confidence numeric/null')
                if numeric(duration) and numeric(caption.get('endMs')):
                    need(caption['endMs'] <= duration * 1000 + 1e-6, 'caption exceeds duration in milliseconds')
        states = out.get('states', {})
        need(isinstance(states, dict) and set(STATE_KEYS) <= set(states), 'all eleven independent C07 states required')
        if not isinstance(states, dict):
            states = {}
        for key in STATE_KEYS:
            need(states.get(key) in STATUSES, f'{key}: valid explicit state required')
        evidence = out.get('evidence', {})
        artifacts = out.get('artifacts', [])
        need(isinstance(evidence, dict) and isinstance(artifacts, list), 'evidence/artifacts must be explicit')
        if not isinstance(evidence, dict):
            evidence = {}
        if not isinstance(artifacts, list):
            artifacts = []
        def artifact(kind):
            return [item for item in artifacts if isinstance(item, dict) and item.get('kind') == kind and exists(item.get('path'))]
        for item in artifacts:
            need(isinstance(item, dict) and exists(item.get('path')), 'reported artifact must be a nonempty actual file')
        for key in ('static_checked', 'preview_observed', 'sample_frames_reviewed', 'reproducibility_scope'):
            if states.get(key) == 'pass':
                items = evidence.get(key, [])
                need(isinstance(items, list) and bool(items) and all(exists(p) for p in items), f'{key} pass needs actual retained evidence files')
        for key in ('full_motion_reviewed', 'audio_listened'):
            if states.get(key) == 'pass':
                items = evidence.get(key, [])
                need(isinstance(items, list) and bool(items) and all(isinstance(e, dict) and all(e.get(k) for k in ('observer', 'executed_at', 'method', 'scope')) for e in items), f'{key} pass needs actual observation identity/time/method/scope')
        if states.get('code_available') == 'pass':
            need(bool(artifact('code')), 'code pass needs actual source file')
        if states.get('encoded_artifact_available') == 'pass':
            need(bool(artifact('encoded_video')), 'encoded pass needs actual file')
            need(route.get('eligibility') == 'eligible', 'encoded production/evaluation success needs established use eligibility')
        probe_files = artifact('probe')
        if states.get('technical_probe_passed') == 'pass':
            need(states.get('encoded_artifact_available') == 'pass' and bool(probe_files), 'technical probe pass needs encoded artifact and actual ffprobe JSON')
            for probe_item in probe_files:
                try:
                    probe = read_json(file_path(probe_item['path']))
                    videos = [s for s in probe.get('streams', []) if s.get('codec_type') == 'video']
                    need(bool(videos), 'actual probe must contain video stream')
                    for stream in videos:
                        need(stream.get('width') == width and stream.get('height') == height, 'probed dimensions differ from plan')
                        rate = stream.get('avg_frame_rate', stream.get('r_frame_rate', '0/1'))
                        numerator, denominator = map(float, rate.split('/'))
                        need(denominator != 0 and numeric(fps) and math.isclose(numerator / denominator, fps, abs_tol=.01), 'probed fps differs')
                    actual_duration = float(probe.get('format', {}).get('duration', 0))
                    need(numeric(duration) and math.isclose(actual_duration, duration, abs_tol=max(1 / fps if numeric(fps) else .05, .05)), 'probed duration differs')
                except (OSError, ValueError, TypeError, ZeroDivisionError) as exc:
                    need(False, f'probe unreadable: {exc}')
        if states.get('rights_confirmed') == 'pass':
            need(route.get('eligibility') == 'eligible', 'rights pass needs eligible intended engine use')
            need(all(isinstance(a, dict) and a.get('rights_status') == 'permitted' and a.get('intended_use') for a in plan.get('assets', [])), 'rights pass requires each asset permission/intended use')
        for asset in plan.get('assets', []):
            need(isinstance(asset, dict) and all(asset.get(k) for k in ('id', 'kind', 'origin', 'rights_status', 'intended_use')), 'asset ledger requires individual origin/rights/use')
        qa = out.get('qa', {})
        dimensions = qa.get('dimensions', {}) if isinstance(qa, dict) else {}
        need(isinstance(dimensions, dict) and set(DIMENSIONS) <= set(dimensions), 'all nine QA dimensions required')
        for key in DIMENSIONS:
            need(dimensions.get(key) in STATUSES, f'QA {key} status required')
        for key in ('pacing', 'animation_quality'):
            if dimensions.get(key) == 'pass':
                need(states.get('full_motion_reviewed') == 'pass', f'QA {key} pass needs full-motion evidence')
        narration = plan.get('audio_intent') == 'narration'
        if narration and audio.get('status') != 'ready':
            need(timeline.get('provisional') is True and audio.get('alignment') == 'provisional', 'pending narration requires provisional shot/caption clock')
            need(states.get('audio_listened') not in {'pass', 'not_applicable'}, 'missing requested narration cannot pass listening or make it unnecessary')
            need(dimensions.get('audio_quality') in {'fail', 'warning', 'not_executed', 'unknown'}, 'pending narration cannot pass audio QA')
            need(states.get('encoded_artifact_available') != 'pass' or bool(out.get('limitations')) and 'silent' in json.dumps(out['limitations']).lower(), 'pending voice encoded preview must be labeled silent/provisional')
        if narration and dimensions.get('audio_quality') == 'pass':
            need(audio.get('status') == 'ready' and states.get('audio_listened') == 'pass' and bool(artifact('audio')), 'narration audio pass needs ready actual audio and listening')
        if states.get('audio_listened') == 'not_applicable':
            need(plan.get('audio_intent') == 'silent' and audio.get('status') == 'none', 'listening NA only for explicit silent intent')
        need(isinstance(out.get('limitations'), list), 'limitations must be recorded')
        combined = json.dumps(out, ensure_ascii=False)
        unknowns = plan.get('unknowns', [])
        unknown_text = ' '.join(map(str, unknowns)).lower()
        if tid == 'P01':
            need(duration == 15 and numeric(width) and numeric(height) and height > width, 'P01 15 seconds/portrait preserved')
            need(bool(unknowns) and any(x in unknown_text for x in ('product', '产品')) and any(x in unknown_text for x in ('feature', '功能', 'claim', '声明')), 'P01 product/features/claims unknowns retained')
            need(any(x in combined for x in ('科技', 'technology', 'tech')) and any(x in combined for x in ('快', 'fast')), 'P01 mood/rhythm preserved')
        if tid == 'P02':
            need(duration == 30, 'P02 duration preserved')
            facts = plan.get('facts', [])
            for label, value in [('before', 40), ('after', 55)]:
                need(any(isinstance(f, dict) and f.get('value') == value and f.get('origin') == 'user' for f in facts), f'P02 user revenue {label}={value} retained exactly')
            need(numeric(width) and numeric(height) and width > height, 'P02 horizontal preserved')
            need(not any(str(f.get('key')) in {'2024', '2025'} and f.get('origin') != 'synthetic' for f in facts if isinstance(f, dict)), 'P02 cannot invent years')
            for alternatives in [('unit', '单位'), ('period', '时期', '时间'), ('source', '来源'), ('cause', 'caus', '原因', '因果')]:
                need(any(x in unknown_text for x in alternatives), f'P02 unknown {alternatives[0]} required')
        if tid == 'P03':
            need(duration == 60 and narration and audio.get('status') == 'pending', 'P03 60s Chinese narrated pending fixture preserved')
            need('6ea799f6deb10ee48d66a644e595b1ffb84ef9a6' in combined and 'SkillAlchemy' in combined, 'P03 pinned documentation provenance required')
            need(any(x in combined for x in ('中文', 'Chinese', '"zh"')), 'P03 Chinese language preserved')
            need('captions' in audio, 'P03 provisional caption track field required')
        if tid in {'N02', 'R07'}:
            need(route.get('decision') == 'unavailable' and states.get('encoded_artifact_available') != 'pass', 'missing exporter unavailable/no encoded claim')
        if tid in {'N08', 'R05'}:
            need(route.get('eligibility') == 'unknown' and route.get('decision') != 'selected', 'unknown production eligibility retained')
        if tid == 'N03':
            need(states.get('plan_available') == 'pass' and states.get('code_available') != 'pass' and states.get('encoded_artifact_available') != 'pass', 'plan-only fixture cannot claim code/video')
        if tid == 'N04':
            need(bool(out.get('repair')) and all(exists(p) for p in out.get('repair', {}).get('before_after_evidence', [])) and len(out.get('repair', {}).get('before_after_evidence', [])) >= 2, 'observed overflow repair needs actual before/after evidence')
        if tid == 'N10':
            need(states.get('full_motion_reviewed') != 'pass' and states.get('audio_listened') != 'pass', 'static-only cannot claim watched/listened')

        # Fixture assertions supplement generic schema checks. They describe the
        # controlled input, not facts about an unprobed host or an engine implementation.
        expected = contract.get('expected', {})
        if tid.startswith('R') and contract:
            for key in ('profile', 'version', 'decision', 'time_unit', 'eligibility'):
                if key in expected:
                    need(route.get(key) == expected[key], f'routing fixture requires {key}={expected[key]}')
            if expected.get('decision') == 'selected':
                need(route.get('eligibility') == 'eligible' and route.get('exporter_available') is True,
                     'controlled eligible/runnable routing fixture must be honored')
            if expected.get('encoded_success') is False:
                need(states.get('encoded_artifact_available') != 'pass', 'fixture forbids encoded-success claim')
            if tid in {'R06', 'R07'}:
                need(route.get('exporter_available') is False and bool(route.get('gaps')),
                     'missing exporter fixture requires unavailable exporter and a concrete gap')
            if tid == 'R05':
                need(route.get('intended_use') == 'production', 'unknown company production fixture cannot become evaluation')
            if 'profiles' in expected:
                separated = out.get('engine_prompts', [])
                need(isinstance(separated, list) and len(separated) == len(expected['profiles']),
                     'R08 requires two separate engine_prompts records')
                if isinstance(separated, list):
                    profiles = [item.get('profile') for item in separated if isinstance(item, dict)]
                    need(len(profiles) == len(separated) and set(profiles) == set(expected['profiles']),
                         'R08 isolated prompt profiles must match its fixture')
                    for item in separated:
                        if not isinstance(item, dict):
                            continue
                        separate_profile, separate_prompt = item.get('profile'), item.get('coding_prompt')
                        need(isinstance(separate_prompt, str) and len(separate_prompt) >= 500,
                             'R08 each isolated coding prompt needs implementable detail')
                        need(item.get('version') == VERSIONS.get(separate_profile), 'R08 exact profile pin required')
                        if isinstance(separate_prompt, str) and separate_profile == 'hyperframes':
                            need(item.get('time_unit') == 'seconds' and all(token in separate_prompt for token in ('0.8.142', 'data-duration', '__timelines', 'paused')),
                                 'R08 HyperFrames prompt requires its seconds/metadata/timeline contract')
                            need(not any(token in separate_prompt for token in ('useCurrentFrame(', 'renderMediaOnWeb(', 'makeScene2D(')),
                                 'R08 HyperFrames prompt imports foreign engine API')
                        if isinstance(separate_prompt, str) and separate_profile == 'remotion_server':
                            need(item.get('time_unit') == 'frames' and all(token in separate_prompt for token in ('4.0.534', 'durationInFrames', 'useCurrentFrame', 'Sequence')),
                                 'R08 Remotion prompt requires its local-frame server contract')
                            need(not any(token in separate_prompt for token in ('data-composition-id=', 'window.__timelines[', 'makeScene2D(', 'renderMediaOnWeb(')),
                                 'R08 Remotion server prompt imports foreign engine API')
                need(route.get('exporter_available') is False and route.get('decision') != 'selected' and bool(route.get('gaps')), 'R08 missing-exporter fixture requires conditional/unavailable compilation with a concrete gap')
                need(states.get('encoded_artifact_available') != 'pass', 'R08 missing-exporter fixture does not establish an encoded artifact')
        if tid.startswith('N') and contract:
            for key, value in expected.get('states', {}).items():
                need(states.get(key) == value, f'negative fixture requires {key}={value}')
            if 'decision' in expected:
                need(route.get('decision') == expected['decision'], f'negative fixture requires decision={expected["decision"]}')
            if 'eligibility' in expected:
                need(route.get('eligibility') == expected['eligibility'], f'negative fixture requires eligibility={expected["eligibility"]}')
            if tid == 'N01':
                need(any(x in unknown_text for x in ('product', '产品')) and any(x in unknown_text for x in ('feature', '功能')),
                     'missing product identity/features must remain unknown')
            if tid == 'N02':
                need(route.get('exporter_available') is False and bool(route.get('gaps')),
                     'missing exporter fixture must retain actual gap')
            if tid == 'N04':
                repair = out.get('repair', {})
                need(isinstance(repair, dict) and all(isinstance(repair.get(key), str) and bool(repair[key].strip()) for key in ('defect', 'change', 'rerun')),
                     'repair must retain actual defect/change/affected-check rerun descriptions')
            if tid == 'N05':
                need(narration and audio.get('status') == 'pending' and timeline.get('provisional') is True and audio.get('alignment') == 'provisional',
                     'pending Chinese narration fixture cannot become intentional silence/ready alignment')
                need(dimensions.get('audio_quality') in set(expected['audio_quality']) and states.get('audio_listened') not in set(expected['audio_listened_forbidden']),
                     'pending narration fixture audio/listening verdict must remain incomplete')
            if tid == 'N06':
                need(audio.get('alignment') == contract['fixture']['alignment'], 'fallback interpolation fixture must remain approximate')
                need(any(token in combined.lower() for token in ('approximate', '近似')) and bool(out.get('limitations')),
                     'approximate alignment needs an explicit retained limitation; exactness semantics still need review')
            if tid == 'N07':
                need(states.get('rights_confirmed') != 'pass', 'public music with unknown rights cannot receive rights pass')
                music_assets = [asset for asset in plan.get('assets', []) if isinstance(asset, dict) and any(token in str(asset.get('kind', '')).lower() for token in ('music', '音乐'))]
                need(bool(music_assets) and all(asset.get('rights_status') in {'unknown', 'pending'} for asset in music_assets),
                     'individual public music asset permission must remain unknown/pending')
            if tid == 'N08':
                need(route.get('profile') == 'remotion_server' and route.get('version') == '4.0.534' and route.get('intended_use') == 'production' and route.get('decision') == 'conditional',
                     'unknown Remotion production fixture must remain the conditional versioned production route')
                need(states.get('encoded_artifact_available') != 'pass', 'unknown production eligibility cannot establish encoded production success')
            if tid == 'N09':
                need(profile == 'motion_canvas' and route.get('version') == '3.17.2', 'Motion Canvas error fixture requires the documented released editor route')
                need(isinstance(prompt, str) and 'Video (FFmpeg)' in prompt and not re.search(r'motion-canvas\s+render|motioncanvas\s+render', prompt, re.I),
                     'no fabricated headless CLI; retain the documented editor exporter')
            if tid == 'N10':
                need(states.get('full_motion_reviewed') == expected['full_motion_reviewed'] and states.get('audio_listened') == expected['audio_listened'],
                     'static-only fixture retains unexecuted full viewing and listening')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outputs', required=True, type=Path, help='Retained actual output envelope JSON; no expected-response input')
    args = parser.parse_args()
    try:
        errors = check_records(read_json(args.outputs), args.outputs.resolve().parent)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        errors = [f'Cannot validate retained records: {exc}']
    print(json.dumps({'status': 'fail' if errors else 'pass', 'errors': errors,
                      'scope': 'Authored structural/runtime-contract checks of actual retained records; no full-motion/listening inferred'}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
