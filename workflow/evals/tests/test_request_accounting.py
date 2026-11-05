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
