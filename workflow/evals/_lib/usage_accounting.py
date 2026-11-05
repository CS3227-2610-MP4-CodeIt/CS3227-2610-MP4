"""Attach request accounting to existing usage report discovery and drilldowns."""
from __future__ import annotations
from typing import Any
from _lib.accounting import record_accounting, combine_accounting, accounting_summary, residual_accounting


def attach_cost(target: dict[str, Any], accounting: dict[str, Any], prefix: str = '') -> None:
    target[prefix + 'est_cost'] = accounting['est_cost']
    target[prefix + 'known_cost'] = accounting['known_cost']
    target[prefix + 'coverage'] = accounting['coverage']


def enrich_session(session: dict[str, Any]) -> None:
    direct = record_accounting(session)
    children = session.get('subagents', [])
    for child in children:
        attach_cost(child, record_accounting(child))
    worker = combine_accounting([direct] + [record_accounting(c) for c in children])
    judges = combine_accounting([record_accounting(j) for j in session.get('judges', [])])
    inclusive = combine_accounting([worker, judges])
    session['direct_accounting'] = direct
    session['inclusive_accounting'] = inclusive
    attach_cost(session, direct, 'parent_')
    attach_cost(session, combine_accounting([record_accounting(c) for c in children]), 'subagent_')
    attach_cost(session, worker, 'worker_')
    attach_cost(session, judges, 'judge_')
    attach_cost(session, inclusive)
    session['actors'] = []
    actor_sources = [session] + children
    for source in actor_sources:
        tid = source['thread_id']
        actor_direct = direct if source is session else record_accounting(source)
        descendants: list[dict[str, Any]] = []
        queue = [tid]
        visited = {tid}
        while queue:
            parent = queue.pop()
            for child in children:
                cid = child['thread_id']
                if child.get('parent_thread_id') == parent and cid not in visited:
                    visited.add(cid)
                    queue.append(cid)
                    descendants.append(record_accounting(child))
        session['actors'].append({
            'thread_id': tid, 'parent_thread_id': source.get('parent_thread_id'),
            'agent_path': source.get('agent_path'),
            'spawn_task_name': source.get('spawn_task_name') or source.get('agent_path'),
            'name': source.get('agent_path') or source.get('spawn_task_name') or source.get('agent_nickname') or ('Main' if source is session else tid),
            'agent_role': source.get('agent_role'), 'model': source.get('model'),
            'direct': actor_direct, 'inclusive': combine_accounting([actor_direct] + descendants)})
    # Root-turn IDs establish membership across workers, including resumed workers.
    # Missing linkage is a visible bucket, never assigned by timestamp/order.
    groups: dict[str, list[dict[str, Any]]] = {}
    for actor in session['actors']:
        for request in actor['direct']['requests']:
            key = request.get('root_turn_id')
            if not key and actor['thread_id'] == session['thread_id']:
                key = request.get('turn_id')
            groups.setdefault(key or 'unattributed', []).append(request)
    session['turns'] = []
    for key, requests in groups.items():
        own = [r for r in requests if r.get('thread_id') == session['thread_id']]
        session['turns'].append({'root_turn_id': key, 'direct': accounting_summary(own),
                                 'inclusive': accounting_summary(requests),
                                 'actors': sorted({r.get('thread_id') or 'unknown' for r in requests})})
    residuals = [residual_accounting(actor['direct']) for actor in session['actors']]
    # Judges have no actor/turn linkage in this view, so retain their observed
    # accounting as unattributed rather than dropping or guessing membership.
    unattributed = combine_accounting(residuals + [judges])
    if unattributed['coverage']['status'] != 'no_calls':
        bucket = next((t for t in session['turns'] if t['root_turn_id'] == 'unattributed'), None)
        if bucket is None:
            bucket = {'root_turn_id': 'unattributed', 'direct': accounting_summary([]),
                      'inclusive': accounting_summary([]), 'actors': []}
            session['turns'].append(bucket)
        bucket['direct'] = combine_accounting([bucket['direct'], residuals[0]])
        bucket['inclusive'] = combine_accounting([bucket['inclusive'], unattributed])
        bucket['actors'] = sorted(set(bucket['actors']) | {
            actor['thread_id'] for actor, residual in zip(session['actors'], residuals)
            if residual['coverage']['status'] != 'no_calls'})


def finalize_usage_accounting(summary: dict[str, Any]) -> dict[str, Any]:
    sessions = summary['sessions']
    evals = summary['harness_evals']
    trials = evals['sessions']
    for session in sessions + trials:
        enrich_session(session)
    real = combine_accounting([s['inclusive_accounting'] for s in sessions])
    offline = combine_accounting([s['inclusive_accounting'] for s in trials])
    attach_cost(summary['totals'], real)
    attach_cost(summary['totals'], combine_accounting([s['direct_accounting'] for s in sessions]), 'parent_')
    attach_cost(summary['totals'], combine_accounting([record_accounting(c) for s in sessions for c in s.get('subagents', [])]), 'subagent_')
    attach_cost(evals['totals'], offline)
    attach_cost(evals['totals'], combine_accounting([combine_accounting([s['direct_accounting']] + [record_accounting(c) for c in s.get('subagents', [])]) for s in trials]), 'worker_')
    attach_cost(evals['totals'], combine_accounting([record_accounting(j) for s in trials for j in s.get('judges', [])]), 'judge_')
    attach_cost(summary['combined_totals'], combine_accounting([real, offline]))
    for skill in summary['skills']:
        # Activity associations have no exclusive usage or costs.
        for key in ('tokens', 'est_cost', 'priced_count'):
            skill.pop(key, None)
        skill['attribution'] = 'Observed activity; no exclusive token or cost attribution'
    for group, source in ((summary['daily'], sessions), (evals['by_skill'], trials)):
        field = 'date' if group is summary['daily'] else 'skill'
        for row in group:
            matching = [s for s in source if s.get('date' if field == 'date' else 'eval_skill') == row[field]]
            attach_cost(row, combine_accounting([s['inclusive_accounting'] for s in matching]))
            if field == 'skill':
                attach_cost(row, combine_accounting([combine_accounting([s['direct_accounting']] + [record_accounting(c) for c in s.get('subagents', [])]) for s in matching]), 'worker_')
                attach_cost(row, combine_accounting([record_accounting(j) for s in matching for j in s.get('judges', [])]), 'judge_')
    # Named workers stay distinct even when their configured role is identical.
    for target, source in ((summary, sessions), (evals, trials)):
        rows = []
        for session in source:
            for actor in session['actors'][1:]:
                direct = actor['direct']
                row = {'role': actor['name'], 'name': actor['name'], 'thread_id': actor['thread_id'],
                       'agent_path': actor['agent_path'], 'agent_role': actor['agent_role'],
                       'configured': False, 'spawns': 1, 'sessions_used': 1,
                       'command_count': next((c.get('command_count', 0) for c in session.get('subagents', []) if c['thread_id'] == actor['thread_id']), 0),
                       'failed_command_count': next((c.get('failed_command_count', 0) for c in session.get('subagents', []) if c['thread_id'] == actor['thread_id']), 0), 'tokens': direct['tokens'],
                       'direct': direct, 'inclusive': actor['inclusive'],
                       'priced_count': direct['coverage']['priced_count']}
                attach_cost(row, direct)
                rows.append(row)
        target['subagents'] = rows
        target['workers'] = [{**actor, 'session_index': i} for i, session in enumerate(source) for actor in session['actors']]
        target['turns'] = [{**turn, 'session_index': i} for i, session in enumerate(source) for turn in session['turns']]
        # Model summaries use each request's model, never the root's final model.
        models: dict[str, list[dict[str, Any]]] = {}
        for session in source:
            for request in session['inclusive_accounting']['requests']:
                models.setdefault(request.get('model') or 'unknown', []).append(request)
        unattributed = combine_accounting([residual_accounting(session['inclusive_accounting']) for session in source])
        target['models'] = []
        for model, requests in models.items():
            accounting = accounting_summary(requests)
            row = {'model': model, 'reasoning_effort': 'per response', 'sessions': sum(any(r.get('model') == (None if model == 'unknown' else model) for r in session['inclusive_accounting']['requests']) for session in source),
                   'turns': len(requests), 'total_calls': len(requests), 'tokens': accounting['tokens'],
                   'priced_count': accounting['coverage']['priced_count']}
            attach_cost(row, accounting)
            target['models'].append(row)
        if unattributed['coverage']['status'] != 'no_calls':
            row = {'model': 'unattributed', 'reasoning_effort': 'unavailable',
                   'sessions': sum(residual_accounting(s['inclusive_accounting'])['coverage']['status'] != 'no_calls' for s in source),
                   'turns': 0, 'total_calls': 0, 'tokens': unattributed['tokens'], 'priced_count': 0}
            attach_cost(row, unattributed)
            target['models'].append(row)
    return summary
