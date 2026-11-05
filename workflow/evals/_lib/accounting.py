"""Read-only request ledger and composable, explicit pricing coverage.

Output includes reasoning. Legacy cumulative observations retain tokens but cannot
establish the context tier of any request and therefore cannot establish cost.
"""
from __future__ import annotations

from typing import Any
from _lib.pricing import estimate_api_cost

TOKEN_FIELDS = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
                'uncached_input_tokens', 'output_tokens', 'reasoning_output_tokens',
                'billed_output_tokens', 'total_tokens')


def normalize_tokens(raw: dict[str, Any]) -> dict[str, int]:
    if not isinstance(raw, dict):
        raise ValueError('invalid usage object')
    values = {}
    for key in ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
                'output_tokens', 'reasoning_output_tokens'):
        value = raw.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError('invalid token count')
        values[key] = value
    if 'input_tokens' not in raw or 'output_tokens' not in raw:
        raise ValueError('missing input/output usage')
    if values['cached_input_tokens'] > values['input_tokens']:
        raise ValueError('cached input exceeds input')
    # A zero-usage fixture/provider may omit a reasoning detail; it is a subset.
    if values['reasoning_output_tokens'] > values['output_tokens']:
        raise ValueError('reasoning exceeds inclusive output')
    values['uncached_input_tokens'] = values['input_tokens'] - values['cached_input_tokens']
    values['billed_output_tokens'] = values['output_tokens']
    values['total_tokens'] = values['input_tokens'] + values['output_tokens']
    return values


def add_tokens(items: list[dict[str, int]]) -> dict[str, int]:
    return {key: sum(item.get(key, 0) or 0 for item in items) for key in TOKEN_FIELDS}


def accounting_summary(requests: list[dict[str, Any]], tokens: dict[str, int] | None = None,
                       unavailable: int = 0, reasons: list[str] | None = None) -> dict[str, Any]:
    priced = [r for r in requests if r.get('est_cost') is not None]
    unknown = sorted({r.get('model') or 'unknown' for r in requests if r.get('est_cost') is None})
    known = round(sum(r['est_cost'] for r in priced), 6)
    count = len(requests) + unavailable
    complete = count > 0 and len(priced) == count
    status = 'no_calls' if not count else 'complete' if complete else 'partial' if priced else 'unavailable'
    return {'requests': requests, 'tokens': tokens if tokens is not None else add_tokens([r['tokens'] for r in requests]),
            'est_cost': known if complete else None, 'known_cost': known if priced else None,
            'coverage': {'status': status, 'request_count': len(requests), 'priced_count': len(priced),
                         'unpriced_count': len(requests) - len(priced), 'unavailable_count': unavailable,
                         'unknown_models': unknown, 'reasons': sorted(set(reasons or []))}}


def combine_accounting(items: list[dict[str, Any]]) -> dict[str, Any]:
    requests = [r for item in items for r in item.get('requests', [])]
    return accounting_summary(requests, add_tokens([i.get('tokens', {}) for i in items]),
                              sum(i.get('coverage', {}).get('unavailable_count', 0) for i in items),
                              [r for i in items for r in i.get('coverage', {}).get('reasons', [])])


def unavailable_accounting(tokens: dict[str, int] | None = None, reason: str = 'usage not captured') -> dict[str, Any]:
    return accounting_summary([], tokens or add_tokens([]), 1, [reason])


def record_accounting(record: dict[str, Any]) -> dict[str, Any]:
    """Never infer request boundaries or models from a legacy summary."""
    return record.get('accounting') or unavailable_accounting(observation_tokens(record.get('token_usage') or record.get('tokens') or {}))


def parse_accounting(events: list[dict[str, Any]], thread_id: str | None, parse_errors: int = 0) -> dict[str, Any]:
    model = turn = root_turn = None
    active_thread = thread_id
    native: list[dict[str, Any]] = []
    legacy: list[dict[str, Any]] = []
    cli: list[dict[str, int]] = []
    latest_total = None
    cumulative_mirrors: list[dict[str, int]] = []
    previous_total = add_tokens([])
    seen: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []
    unavailable = parse_errors
    if parse_errors:
        reasons.append("malformed JSON records")
    native_seen = False
    legacy_gap = False
    legacy_reset = False
    for index, event in enumerate(events):
        payload = event.get('payload', event)
        if not isinstance(payload, dict):
            continue
        kind = event.get('type')
        if kind == 'session_meta':
            active_thread = payload.get('id') or active_thread
            continue
        if kind == 'thread.started':
            active_thread = event.get('thread_id') or active_thread
            continue
        owner = payload.get('thread_id') or event.get('thread_id') or active_thread
        if thread_id and owner and owner != thread_id:
            continue
        if kind == 'turn_context':
            model = payload.get('model')  # do not carry a previous model into an unknown turn
            turn = payload.get('turn_id')
            root_turn = payload.get('root_turn_id')
            continue
        if kind == 'token_usage_record' or payload.get('type') == 'token_usage_record':
            native_seen = True
            try:
                tokens = normalize_tokens(payload.get('usage') or {})
            except (ValueError, TypeError):
                unavailable += 1
                reasons.append('malformed request usage')
                continue
            rid = payload.get('response_id')
            if not isinstance(rid, str) or not rid:
                unavailable += 1
                reasons.append('missing response identity')
                continue
            if rid in seen:
                if seen[rid]['tokens'] != tokens:
                    unavailable += 1
                    reasons.append('conflicting response mirror')
                continue
            rmodel = payload.get('model') or model
            request = {'response_id': rid, 'thread_id': owner or thread_id,
                       'turn_id': payload.get('turn_id') or turn,
                       'root_turn_id': payload.get('root_turn_id') or root_turn,
                       'session_id': payload.get('session_id'),
                       'timestamp': event.get('timestamp'), 'model': rmodel,
                       'source': 'token_usage_record', 'tokens': tokens,
                       'est_cost': estimate_api_cost(tokens, rmodel)}
            seen[rid] = request
            native.append(request)
        elif kind == 'event_msg' and payload.get('type') == 'token_count':
            info = payload.get('info') or payload
            if not isinstance(info, dict):
                legacy_gap = True
                continue
            raw_total = info.get('total_token_usage')
            if not isinstance(raw_total, dict):
                continue
            try:
                total = normalize_tokens(raw_total)
            except (ValueError, TypeError):
                legacy_gap = True
                continue
            cumulative_mirrors.append(total)
            if legacy_reset:
                continue  # later growth cannot establish the reset window's scope
            if latest_total is not None and any(total[k] < latest_total[k] for k in TOKEN_FIELDS):
                legacy_reset = True
                legacy_gap = True
                reasons.append('cumulative mirror reset; scope unavailable')
                continue
            if latest_total == total:
                continue  # repeated token_count mirror, not another response
            latest_total = total
            raw_last = info.get('last_token_usage')
            try:
                last = normalize_tokens(raw_last or {})
            except (ValueError, TypeError):
                legacy_gap = True
                previous_total = total
                continue
            expected = add_tokens([previous_total, last])
            if any(expected[k] != total[k] for k in TOKEN_FIELDS):
                legacy_gap = True
            else:
                legacy.append({'response_id': f'legacy:{index}', 'thread_id': owner or thread_id,
                               'turn_id': payload.get('turn_id') or turn,
                               'root_turn_id': payload.get('root_turn_id') or root_turn,
                               'timestamp': event.get('timestamp'), 'model': model,
                               'source': 'reconciled token_count.last', 'tokens': last,
                               'est_cost': estimate_api_cost(last, model)})
            previous_total = total
        elif kind == 'turn.completed' and isinstance(event.get('usage'), dict):
            try:
                cli.append(normalize_tokens(event['usage']))
            except (ValueError, TypeError):
                legacy_gap = True
    if native_seen:
        tokens = add_tokens([r['tokens'] for r in native])
        # Native thread totals expose missing response records without charging
        # cumulative mirrors as requests. Resets/gaps remain explicitly partial.
        totals = []
        for event in events:
            p = event.get('payload') or {}
            if event.get('type') == 'token_usage_record' and isinstance(p, dict) and p.get('thread_id') == thread_id:
                try:
                    totals.append(normalize_tokens(p.get('thread_token_usage') or {}))
                except (ValueError, TypeError):
                    pass
        if not totals and cumulative_mirrors:
            reset = any(any(current[k] < previous[k] for k in TOKEN_FIELDS)
                        for previous, current in zip(cumulative_mirrors, cumulative_mirrors[1:]))
            if reset:
                unavailable += 1
                reasons.append('cumulative mirror reset; scope unavailable')
            else:
                totals = cumulative_mirrors
        if totals and any(tokens[k] != totals[-1][k] for k in TOKEN_FIELDS):
            unavailable += 1
            reasons.append('request ledger does not reconcile with thread total')
            # Cumulative mirrors supply token/coverage evidence, never another
            # request or a context tier. Owned native thread totals take precedence.
            tokens = {k: max(tokens[k], totals[-1][k]) for k in TOKEN_FIELDS}
        return accounting_summary(native, tokens, unavailable, reasons)
    if legacy and not legacy_gap:
        return accounting_summary(legacy, unavailable=unavailable, reasons=reasons)
    tokens = latest_total or (add_tokens(cli) if cli else add_tokens([]))
    # Keep the last compatible cumulative observation and accepted request
    # evidence. A reset never replaces them or starts another priced window.
    ledger = add_tokens([request['tokens'] for request in legacy])
    tokens = {key: max(tokens.get(key, 0), ledger[key]) for key in TOKEN_FIELDS}
    # Boundary uncertainty adds to parse gaps; it must not replace them.
    reasons.append('incomplete request boundaries' if latest_total or cli else 'usage not captured')
    return accounting_summary(legacy, tokens, unavailable + 1, reasons)



def agent_path(events: list[dict[str, Any]], thread_id: str | None) -> str | None:
    for event in events:
        payload = event.get('payload')
        if event.get('type') != 'session_meta' or not isinstance(payload, dict) or payload.get('id') != thread_id:
            continue
        value: Any = payload
        for key in ('source', 'subagent', 'thread_spawn', 'agent_path'):
            value = value.get(key) if isinstance(value, dict) else None
        if isinstance(value, str):
            return value
    return None


def observation_tokens(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize historical derived fields without modifying retained evidence."""
    tokens = dict(raw)
    output = tokens.get('output_tokens')
    input_tokens = tokens.get('input_tokens')
    if isinstance(output, (int, float)) and not isinstance(output, bool):
        tokens['billed_output_tokens'] = output
        if isinstance(input_tokens, (int, float)) and not isinstance(input_tokens, bool):
            tokens['total_tokens'] = input_tokens + output
    return tokens


def residual_accounting(accounting: dict[str, Any]) -> dict[str, Any]:
    """Unlinked observations after known requests, without inventing a model/turn."""
    observed = accounting.get('tokens', {})
    ledger = add_tokens([r['tokens'] for r in accounting.get('requests', [])])
    residual = {key: max(observed.get(key, 0) - ledger[key], 0) for key in TOKEN_FIELDS}
    coverage = accounting.get('coverage', {})
    unavailable = coverage.get('unavailable_count', 0)
    if any(residual.values()) and not unavailable:
        unavailable = 1
    return accounting_summary([], residual, unavailable, coverage.get('reasons', []))
