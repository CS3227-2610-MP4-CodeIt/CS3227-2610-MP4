"""Observable request accounting contracts; no network or live report writes."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib.accounting import parse_accounting, combine_accounting


def native(rid, inp=150000, out=153, model=None, thread='root', turn='t', root='rt'):
    return {'type': 'token_usage_record', 'timestamp': '2026-11-04T01:00:00Z', 'payload': {
        'thread_id': thread, 'turn_id': turn, 'root_turn_id': root, 'response_id': rid,
        **({'model': model} if model else {}),
        'usage': {'input_tokens': inp, 'output_tokens': out, 'reasoning_output_tokens': min(17, out)}}}


def test_native_response_model_switch_dedup_and_foreign_mirrors():
    a = native('a', inp=21111)
    records = [{'type': 'turn_context', 'payload': {'model': 'gpt-6.1-sol'}}, a, a,
               {'type': 'turn_context', 'payload': {'model': 'gpt-6-luna'}}, native('b'),
               native('foreign', thread='other'), {'type': 'turn.completed', 'usage': {'input_tokens': 999999, 'output_tokens': 999}}]
    result = parse_accounting(records, 'root')
    assert len(result['requests']) == 2
    assert [r['model'] for r in result['requests']] == ['gpt-6.1-sol', 'gpt-6-luna']
    assert result['requests'][0]['tokens']['total_tokens'] == 21264
    assert result['tokens']['billed_output_tokens'] == 306
    assert result['coverage']['status'] == 'complete'


def test_pricing_each_request_before_aggregation():
    split = parse_accounting([native('a', model='gpt-6.1-sol'), native('b', model='gpt-6.1-sol')], 'root')
    whole = parse_accounting([native('c', inp=300000, out=306, model='gpt-6.1-sol')], 'root')
    assert split['est_cost'] == 0.60306
    assert whole['est_cost'] == 1.20459


def test_unknown_missing_and_zero_are_distinct():
    known = parse_accounting([native('a', model='gpt-6.1-sol')], 'root')
    unknown = parse_accounting([native('b', model='future-model')], 'root')
    missing = parse_accounting([], 'missing')
    zero = parse_accounting([native('zero', inp=0, out=0, model='gpt-6.1-sol')], 'root')
    assert zero['est_cost'] == 0
    assert missing['est_cost'] is None
    mixed = combine_accounting([known, unknown, missing])
    assert mixed['est_cost'] is None
    assert mixed['known_cost'] == known['est_cost']
    assert mixed['coverage']['status'] == 'partial'
    assert mixed['coverage']['unknown_models'] == ['future-model']
    assert combine_accounting([])['coverage']['status'] == 'no_calls'


def test_legacy_boundaries_must_reconcile_and_cumulative_never_priced():
    u = {'input_tokens': 150000, 'output_tokens': 10}
    def tc(total, last=None):
        return {'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {
            'total_token_usage': total, **({'last_token_usage': last} if last is not None else {})}}}
    ctx = {'type': 'turn_context', 'payload': {'model': 'gpt-6.1-sol'}}
    cumulative = parse_accounting([ctx, tc(u)], 'root')
    assert cumulative['tokens']['input_tokens'] == 150000
    assert cumulative['est_cost'] is None
    valid = parse_accounting([ctx, tc(u, u), tc({'input_tokens': 300000, 'output_tokens': 20}, u)], 'root')
    assert valid['est_cost'] == 0.6002
    gap = parse_accounting([ctx, tc(u, u), tc({'input_tokens': 450000, 'output_tokens': 30}, u)], 'root')
    assert gap['est_cost'] is None
    assert gap['coverage']['status'] == 'partial'


def test_malformed_usage_and_missing_model_are_unavailable():
    bad = native('bad'); bad['payload']['usage']['input_tokens'] = 'bad'
    result = parse_accounting([bad, native('unknown')], 'root')
    assert result['est_cost'] is None
    assert result['coverage']['unavailable_count'] >= 1


def test_nested_named_workers_turns_and_skill_activity(tmp_path):
    from _lib.usage import parse_session_rollout, build_project_usage, render_usage_html, render_usage_markdown
    project = tmp_path / 'project'; evals = project / 'workflow' / 'evals'; evals.mkdir(parents=True)
    for skill in ('plan-task', 'implement-task'):
        path = project / '.agents' / 'skills' / skill / 'SKILL.md'; path.parent.mkdir(parents=True); path.write_text('fixture')
    def rollout(tid, parent=None, path=None, requests=()):
        meta = {'id': tid, 'cwd': str(project)}
        if parent:
            meta['source'] = {'subagent': {'thread_spawn': {'parent_thread_id': parent, 'agent_path': path}}}
        events = [{'type': 'session_meta', 'payload': meta},
                  {'type': 'turn_context', 'payload': {'model': 'gpt-6.1-sol'}}, *requests]
        if tid == 'root':
            events += [{'type': 'item.completed', 'item': {'type': 'command_execution', 'command': 'cat .agents/skills/plan-task/SKILL.md .agents/skills/implement-task/SKILL.md', 'exit_code': 0}}]
        file = tmp_path / (tid + '.jsonl'); file.write_text('\n'.join(json.dumps(e) for e in events))
        return str(file), parse_session_rollout(file)
    records = dict([rollout('root', requests=[native('r1', inp=100, root='first'), native('r2', inp=200, turn='t2', root='second')]),
                    rollout('child', 'root', '/root/worker<script>', [native('c1', inp=300, thread='child', root='first'), native('c2', inp=400, thread='child', turn='resume', root='second')]),
                    rollout('nested', 'child', '/root/worker/nested', [native('n1', inp=500, thread='nested', root='first')])])
    summary = build_project_usage(records, project, evals)
    session = summary['sessions'][0]
    assert session['parent_token_usage']['input_tokens'] == 300
    assert session['token_usage']['input_tokens'] == 1500
    assert [t['inclusive']['tokens']['input_tokens'] for t in session['turns']] == [900, 600]
    actors = {a['thread_id']: a for a in session['actors']}
    assert actors['child']['direct']['tokens']['input_tokens'] == 700
    assert actors['child']['inclusive']['tokens']['input_tokens'] == 1200
    assert len(summary['subagents']) == 2
    assert len(summary['skills']) == 2
    assert all('tokens' not in s and 'est_cost' not in s for s in summary['skills'])
    html = render_usage_html(summary)
    assert 'worker&lt;script&gt;' in html and 'worker<script>' not in html
    assert 'Turns · direct and inclusive usage' in html
    assert 'Timeline' in html and 'Context' in html
    assert 'Request accounting' in render_usage_markdown(summary)


def test_native_rollout_metrics_share_identical_arithmetic(tmp_path):
    from _lib.trace import trace_metrics, read_rollout_metrics
    from _lib.usage import parse_session_rollout
    events = [{'type': 'session_meta', 'payload': {'id': 'root'}}, native('a', inp=21111, model='gpt-6.1-sol')]
    path = tmp_path / 'trace.jsonl'; path.write_text('\n'.join(json.dumps(e) for e in events))
    online = parse_session_rollout(path)
    offline = trace_metrics(path)
    assert online['accounting'] == offline['accounting'] == read_rollout_metrics(path)['accounting']
    assert offline['input_tokens'] + offline['billed_output_tokens'] == 21264


def test_missing_worker_and_unknown_judge_are_not_priced_from_run_model(tmp_path):
    from _lib.usage import build_project_usage
    project = tmp_path / 'p'; evals = project / 'workflow' / 'evals'
    trial = evals / 'skill' / 'runs' / 'experiment-001' / 'trials' / 'case' / 'baseline' / 'trial-01'
    judge = trial / 'grades' / 'semantic' / 'judge-01'; judge.mkdir(parents=True)
    (trial / 'run.json').write_text(json.dumps({'resolved_model': 'gpt-6.1-sol'}))
    (judge / 'trace.jsonl').write_text(json.dumps(native('j', thread='judge')))
    summary = build_project_usage({}, project, evals)
    trial_summary = summary['harness_evals']['sessions'][0]
    assert trial_summary['judges'][0]['model'] is None
    assert trial_summary['est_cost'] is None
    assert summary['harness_evals']['totals']['coverage']['unavailable_count'] == 1
    assert summary['harness_evals']['totals']['coverage']['unknown_models'] == ['unknown']


def test_missing_rate_components_and_context_tiers_are_unpriced():
    from _lib.pricing import estimate_api_cost
    assert estimate_api_cost({'uncached_input_tokens': 300000}, 'gpt-5.4') is None
    assert estimate_api_cost({'cached_input_tokens': 100}, 'gpt-5.5-pro') is None
    assert estimate_api_cost({'cache_write_input_tokens': 100}, 'gpt-5.5') is None


def test_native_gap_preserves_tokens_and_partial_known_subtotal():
    event = native('after-gap', inp=100, out=20, model='gpt-6.1-sol')
    event['payload']['thread_token_usage'] = {'input_tokens': 300, 'output_tokens': 40}
    accounting = parse_accounting([event], 'root')
    assert accounting['tokens']['input_tokens'] == 300
    assert accounting['tokens']['output_tokens'] == 40
    assert accounting['est_cost'] is None
    assert accounting['known_cost'] == 0.0004
    assert accounting['coverage']['status'] == 'partial'


def test_historical_derived_output_normalized_without_rewriting_source(tmp_path):
    from copy import deepcopy
    from _lib.report import aggregate, write_report
    from _lib.compare import compare_cell
    result = {'test_case': 'old', 'configuration': 'baseline', 'score': 100, 'overall_pass': True,
              'trial': 1, 'run_directory': 'trials/old', 'tokens': {
                  'input_tokens': 21111, 'output_tokens': 153, 'reasoning_output_tokens': 17,
                  'billed_output_tokens': 170}}
    before = deepcopy(result)
    aggregates = aggregate([result])
    cell = aggregates['cells']['old']['baseline']
    assert cell['mean_tokens']['billed_output_tokens'] == 153
    old = {'mean_tokens': {'output_tokens': 153, 'reasoning_output_tokens': 17, 'billed_output_tokens': 170}}
    assert compare_cell(old, old)['billed_output_tokens']['old'] == 153
    report = write_report(tmp_path, {'skill': 'old', 'status': 'completed', 'overall_pass': True,
                                     'mean_score': 100, 'passed_trials': 1, 'worker_trials': 1}, aggregates, [result])
    assert '| 153 |' in report.read_text()
    assert '| 170 |' not in report.read_text()
    assert result == before


def test_unavailable_trial_cost_is_not_excluded_from_comparison_mean():
    from _lib.usage import derive_experiment_comparison
    trials = [{'test_case': 'c', 'configuration': 'baseline', 'est_cost': cost,
               'token_usage': {'billed_output_tokens': 10}} for cost in (1, None)]
    comparison = derive_experiment_comparison(trials)[0]
    assert comparison['baseline']['mean_cost'] is None


def test_parse_gap_is_partial_and_preserves_known_subtotal():
    accounting = parse_accounting([native('a', model='gpt-6.1-sol')], 'root', parse_errors=1)
    assert accounting['est_cost'] is None
    assert accounting['known_cost'] is not None
    assert accounting['coverage']['unavailable_count'] == 1


def test_legacy_parse_errors_survive_every_return_and_combination():
    ctx = {'type': 'turn_context', 'payload': {'model': 'gpt-6.1-sol'}}
    usage = {'input_tokens': 10, 'output_tokens': 1}
    event = {'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {
        'total_token_usage': usage, 'last_token_usage': usage}}}
    reconciled = parse_accounting([ctx, event], 'root', parse_errors=2)
    assert reconciled['coverage']['status'] == 'partial'
    assert reconciled['est_cost'] is None and reconciled['known_cost'] == 0.00003
    assert reconciled['coverage']['unavailable_count'] == 2
    del event['payload']['info']['last_token_usage']
    cumulative = parse_accounting([ctx, event], 'root', parse_errors=3)
    assert cumulative['coverage']['unavailable_count'] == 4
    assert 'malformed JSON records' in cumulative['coverage']['reasons']
    assert combine_accounting([reconciled, cumulative])['coverage']['unavailable_count'] == 6


def test_native_cumulative_mirrors_preserve_owner_gaps_without_repricing():
    def mirror(inp, out, owner='root'):
        return {'type': 'event_msg', 'payload': {'type': 'token_count', 'thread_id': owner,
            'info': {'total_token_usage': {'input_tokens': inp, 'output_tokens': out, 'reasoning_output_tokens': min(17, out)}}}}
    request = native('r', inp=100, out=20, model='gpt-6.1-sol')
    gap = parse_accounting([request, mirror(300, 40)], 'root')
    assert gap['tokens']['input_tokens'] == 300
    assert gap['coverage']['status'] == 'partial'
    assert gap['known_cost'] == 0.0004 and gap['est_cost'] is None
    assert len(gap['requests']) == 1
    assert parse_accounting([request, mirror(100, 20)], 'root')['coverage']['status'] == 'complete'
    assert parse_accounting([request, mirror(300, 40, 'foreign')], 'root')['tokens']['input_tokens'] == 100
    reset = parse_accounting([request, mirror(300, 40), mirror(10, 1)], 'root')
    assert reset['tokens']['input_tokens'] == 100  # reset scope cannot be assumed to match
    assert reset['coverage']['status'] == 'partial'
    assert parse_accounting([request, {'type': 'turn.completed', 'usage': {'input_tokens': 900, 'output_tokens': 90}}], 'root')['tokens']['input_tokens'] == 100


def test_residual_observations_reconcile_turn_and_model_buckets(tmp_path):
    from _lib.usage import build_project_usage, render_usage_html, render_usage_markdown
    project = tmp_path / 'p'; evals = project / 'workflow' / 'evals'; evals.mkdir(parents=True)
    request = native('r', inp=100, out=20, model='gpt-6.1-sol')
    request['payload']['thread_token_usage'] = {'input_tokens': 300, 'output_tokens': 40}
    accounting = parse_accounting([request], 'root', parse_errors=1)
    root = {'thread_id': 'root', 'cwd': str(project), 'accounting': accounting,
            'token_usage': accounting['tokens'], 'subagents': [{'thread_id': 'missing'}]}
    from _lib.accounting import normalize_tokens
    child_tokens = normalize_tokens({'input_tokens': 50, 'output_tokens': 5})
    child = {'thread_id': 'legacy', 'parent_thread_id': 'root', 'cwd': str(project),
             'token_usage': child_tokens}
    summary = build_project_usage({'root': root, 'child': child}, project, evals)
    session = summary['sessions'][0]
    unattributed = next(t for t in session['turns'] if t['root_turn_id'] == 'unattributed')
    assert unattributed['inclusive']['tokens']['input_tokens'] == 250
    assert unattributed['inclusive']['coverage']['unavailable_count'] == 4  # gap, parse error, legacy, missing child
    assert unattributed['inclusive']['est_cost'] is None
    assert sum(t['inclusive']['tokens']['input_tokens'] for t in session['turns']) == 350
    assert sum(m['tokens']['input_tokens'] for m in summary['models']) == 350
    unknown = next(m for m in summary['models'] if m['model'] == 'unattributed')
    assert unknown['coverage']['unavailable_count'] == 4
    assert next(m for m in summary['models'] if m['model'] == 'gpt-6.1-sol')['est_cost'] == 0.0004
    assert 'unattributed' in render_usage_html(summary)
    assert 'unattributed' in render_usage_markdown(summary)


def test_markdown_metadata_is_inert_while_json_stays_raw(tmp_path):
    from _lib.usage import build_project_usage, render_usage_html, render_usage_markdown
    from _lib.report import aggregate, write_report
    from _lib.common import markdown_metadata
    hostile = 'model`|[link](https://invalid)\n\n## Forged coverage\n<img src=x onerror=bad()>'
    project = tmp_path / 'p'; evals = project / 'workflow' / 'evals'; evals.mkdir(parents=True)
    request = native('r', inp=100, out=20, model=hostile, root=hostile)
    accounting = parse_accounting([request], 'root')
    record = {'thread_id': 'root', 'cwd': str(project), 'accounting': accounting,
              'token_usage': accounting['tokens'], 'agent_nickname': hostile}
    summary = build_project_usage({'root': record}, project, evals)
    from _lib.usage_accounting import enrich_session
    summary['sessions'][0]['agent_nickname'] = hostile
    enrich_session(summary['sessions'][0])
    markdown = render_usage_markdown(summary)
    result = {'test_case': 'case', 'configuration': 'baseline', 'trial': 1, 'score': 100,
              'overall_pass': True, 'run_directory': 'trials/x', 'tokens': accounting['tokens'],
              'accounting': accounting, 'resolved_model': hostile}
    report = write_report(tmp_path, {'skill': 'fixture', 'status': 'completed', 'overall_pass': True,
        'mean_score': 100, 'passed_trials': 1, 'worker_trials': 1}, aggregate([result]), [result]).read_text()
    for text in (markdown, report):
        assert '\n## Forged coverage' not in text and '<img' not in text
        assert markdown_metadata(hostile) in text
    assert summary['models'][0]['model'] == hostile
    assert summary['sessions'][0]['actors'][0]['name'] == hostile
    assert '<img' not in render_usage_html(summary)


def test_legacy_reset_conserves_all_fields_without_pricing_later_windows(tmp_path):
    """C5: accepted requests survive reset; ambiguous resumed counters add no charge."""
    from _lib.accounting import TOKEN_FIELDS, normalize_tokens, add_tokens
    from _lib.usage import build_project_usage
    base = normalize_tokens({'input_tokens': 300, 'cached_input_tokens': 100,
        'cache_write_input_tokens': 10, 'output_tokens': 30, 'reasoning_output_tokens': 15})
    variants = [
        {'input_tokens': 10, 'cached_input_tokens': 2, 'cache_write_input_tokens': 1,
         'output_tokens': 1, 'reasoning_output_tokens': 0},
        {'input_tokens': 0, 'output_tokens': 0},
        {**base, 'input_tokens': 310, 'cached_input_tokens': 50, 'output_tokens': 31},
        {**base, 'input_tokens': 310, 'cached_input_tokens': 150, 'output_tokens': 31},
        {**base, 'input_tokens': 310, 'cache_write_input_tokens': 1, 'output_tokens': 31},
        {**base, 'input_tokens': 310, 'output_tokens': 20},
        {**base, 'input_tokens': 310, 'output_tokens': 31, 'reasoning_output_tokens': 1},
    ]
    ctx = {'type': 'turn_context', 'payload': {'model': 'gpt-6.1-sol', 'turn_id': 'turn'}}
    def counter(total, last=None):
        return {'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {
            'total_token_usage': total, **({'last_token_usage': last} if last is not None else {})}}}
    project = tmp_path / 'p'; evals = project / 'workflow' / 'evals'; evals.mkdir(parents=True)
    increment = normalize_tokens({'input_tokens': 1000, 'cached_input_tokens': 500,
        'cache_write_input_tokens': 100, 'output_tokens': 100, 'reasoning_output_tokens': 50})
    known = parse_accounting([ctx, counter(base, base)], 'root')['est_cost']
    for raw_reset in variants:
        reset = normalize_tokens(raw_reset)
        continuation = add_tokens([reset, increment])
        for accepted in (False, True):
            for continued in (False, True):
                events = [ctx, counter(base, base if accepted else None), counter(reset, reset)]
                if continued:
                    events.append(counter(continuation, increment))
                accounting = parse_accounting(events, 'root', parse_errors=2)
                assert accounting['tokens'] == base
                assert len(accounting['requests']) == int(accepted)
                assert accounting['known_cost'] == (known if accepted else None)
                assert accounting['est_cost'] is None
                assert accounting['coverage']['unavailable_count'] >= 3
                assert 'malformed JSON records' in accounting['coverage']['reasons']
                assert any('reset' in reason for reason in accounting['coverage']['reasons'])
                summary = build_project_usage({'root': {'thread_id': 'root', 'cwd': str(project),
                    'token_usage': accounting['tokens'], 'accounting': accounting}}, project, evals)
                session = summary['sessions'][0]
                for key in TOKEN_FIELDS:
                    expected = base[key]
                    assert session['actors'][0]['direct']['tokens'][key] == expected
                    assert session['inclusive_accounting']['tokens'][key] == expected
                    assert sum(t['inclusive']['tokens'][key] for t in session['turns']) == expected
                    assert sum(m['tokens'][key] for m in summary['models']) == expected
                assert summary['totals']['est_cost'] is None
                assert summary['totals']['known_cost'] == (known if accepted else None)
