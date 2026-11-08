"""Standalone HTML presentation for collected experiment comparisons."""

from __future__ import annotations

import html
from typing import Callable

from _lib.pricing import PRICING_AS_OF, PRICING_SOURCE, format_cost, format_cost_delta, format_delta
from _lib.timing import format_seconds, time_delta


def _number(value) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        return f"{value:,.2f}".rstrip("0").rstrip(".")
    return str(value)


def _tone(verdict: str | None) -> str:
    return "good" if verdict == "improved" else "bad" if verdict == "regressed" else "neutral"


def _cost_verdict(old, new) -> str:
    if old is None or new is None:
        return "unknown"
    if old == new:
        return "unchanged"
    return "improved" if new < old else "regressed"


def _panel(
    *, version: str, experiment: str, model, effort, config: str,
    requested_trials, diff: dict,
) -> str:
    side = "old" if version == "v1" else "new"
    count = diff.get(f"n_{side}", 0)
    passed = diff.get(f"passed_{side}")
    passed_text = f"{passed} / {count}" if count and passed is not None else "N/A"
    score = diff.get("score", {}).get(side)
    time = diff.get("worker_time", {}).get(side)
    billed = diff.get("billed_output_tokens", {}).get(side)
    cost = diff.get(f"_cost_{side}")
    effort_label = f"{effort} effort" if effort else "effort not captured"
    metadata = (
        f"{model or 'Model not captured'} · {effort_label} · "
        f"{config} · {count} trial{'s' if count != 1 else ''}"
    )
    planned = _number(requested_trials) if requested_trials is not None else "not captured"
    measurements = (
        ("Passes", passed_text),
        ("Mean worker time", format_seconds(time)),
        ("Mean billed output", _number(billed)),
        ("Worker cost / trial", format_cost(cost)),
    )
    metrics = "".join(
        f"<div class='run-row'><span>{html.escape(label)}</span>"
        f"<strong>{html.escape(value)}</strong></div>"
        for label, value in measurements
    )
    return (
        f"<article class='run-panel {version}'><header class='run-header'>"
        f"<span class='version-label'>{version.upper()}</span>"
        f"<h3>{html.escape(experiment)}</h3><p>{html.escape(metadata)}</p>"
        f"<p>Configured trials per cell: {html.escape(planned)}</p></header>"
        f"<div class='run-score'><strong>{html.escape(_number(score))}</strong>"
        f"<span>{'/ 100 mean score' if score is not None else 'mean score not available'}</span></div>"
        f"<div class='run-rows'>{metrics}</div></article>"
    )


def _changes(diff: dict) -> str:
    score = diff.get("score", {})
    passes = diff.get("pass_rate", {})
    time = diff.get("worker_time", {})
    billed = diff.get("billed_output_tokens", {})
    old_cost, new_cost = diff.get("_cost_old"), diff.get("_cost_new")
    axes = (
        ("Score", "Higher is better", format_delta(score.get("old"), score.get("new")), score.get("verdict")),
        ("Pass rate", "Higher is better", format_delta(passes.get("old"), passes.get("new")), passes.get("verdict")),
        ("Mean worker time", "Lower is better", time_delta(time.get("old"), time.get("new")), time.get("verdict")),
        ("Mean billed output", "Lower is better · tokens", format_delta(billed.get("old"), billed.get("new")), billed.get("verdict")),
        ("Worker cost / trial", "Lower is better · API estimate", format_cost_delta(old_cost, new_cost), _cost_verdict(old_cost, new_cost)),
    )
    rows = []
    for label, direction, change, verdict in axes:
        verdict = verdict or "unknown"
        rows.append(
            f"<div class='change-row'><strong>{html.escape(label)}</strong>"
            f"<span class='change-direction'>{html.escape(direction)}</span>"
            f"<div class='change-value {_tone(verdict)}'><strong>{html.escape(change)}</strong>"
            f"<span>{html.escape(verdict)}</span></div></div>"
        )
    return "".join(rows)


def render_comparison_body(
    skill: str, old_id: str, new_id: str, partition: dict, rows: list[dict],
    skill_diff: list[str], summary: dict, provenance: dict,
    render_case_details: Callable[[dict], str],
) -> str:
    """Render all report sections from the same structured data as Markdown."""
    config = provenance.get("config") or "with-skill"
    old_model, new_model = provenance.get("old_model"), provenance.get("new_model")
    old_effort, new_effort = provenance.get("old_effort"), provenance.get("new_effort")
    trials = provenance.get("trials") or {}

    warnings = []
    if not old_model or not new_model or not old_effort or not new_effort:
        warnings.append("Model or reasoning effort was not captured for both runs. Check the setup before attributing differences to the skill.")
    elif old_model != new_model or old_effort != new_effort:
        warnings.append("Model or reasoning effort differs between runs. Changes in scores or resource use may also reflect that difference.")
    if partition.get("only_old") or partition.get("only_new"):
        warnings.append("The test-case sets differ. Only cases present in both experiments can be compared.")
    for row in rows:
        if row.get("confounds"):
            warnings.append(f"{row['test_case']}: " + "; ".join(row["confounds"]) + ".")
    warnings_html = "".join(
        f"<aside class='notice'><strong>Interpret this comparison with care</strong><p>{html.escape(warning)}</p></aside>"
        for warning in dict.fromkeys(warnings)
    )

    score_counts = [("improved", "improved"), ("regressed", "regressed"), ("unchanged", "unchanged")]
    if summary.get("unknown", 0):
        score_counts.append(("unknown", "unknown"))
    counts_html = "".join(
        f"<span><strong>{summary.get(key, 0)}</strong> {label}</span>" for key, label in score_counts
    )
    summary_html = (
        f"<section class='card summary-card'><div><h2>Score outcomes</h2>"
        f"<p>{len(partition.get('both', []))} shared case(s) · {len(rows)} compared</p></div>"
        f"<div class='summary-counts'>{counts_html}</div></section>"
    )

    case_sections = []
    for row in rows:
        diff = row["diff"]
        case = str(row["test_case"])
        score_verdict = diff.get("score", {}).get("verdict") or "unknown"
        n_old, n_new = diff.get("n_old", 0), diff.get("n_new", 0)
        common = {"config": config, "diff": diff}
        old_panel = _panel(version="v1", experiment=old_id, model=old_model, effort=old_effort,
                           requested_trials=trials.get("old"), **common)
        new_panel = _panel(version="v2", experiment=new_id, model=new_model, effort=new_effort,
                           requested_trials=trials.get("new"), **common)
        case_sections.append(
            f"<section class='case-section'><div class='case-heading'><div><h2>Case comparison</h2>"
            f"<p class='case-name'>{html.escape(case)}</p><p class='muted'>{html.escape(str(n_old))} v1 trial(s) · {html.escape(str(n_new))} v2 trial(s) · values are cell means</p></div>"
            f"<span class='score-verdict {_tone(score_verdict)}'>Score: {html.escape(score_verdict)}</span></div>"
            f"<div class='run-panels'>{old_panel}{new_panel}</div>"
            f"<section class='card changes'><header><h3>What changed</h3><p>v2 compared with v1; score and resource verdicts are independent.</p></header>"
            f"<div class='change-list'>{_changes(diff)}</div></section>"
            f"<details class='card disclosure case-detail'><summary>All metrics and individual trials</summary>"
            f"<div class='disclosure-body'>{render_case_details(row)}</div></details></section>"
        )

    missing = sorted(set(partition.get("both", [])) - {r["test_case"] for r in rows})
    extras = []
    for label, cases in (("Only in v1", partition.get("only_old", [])), ("Only in v2", partition.get("only_new", [])), ("Missing configuration data", missing)):
        if cases:
            extras.append(f"<div><strong>{label}</strong><span>{', '.join(html.escape(str(c)) for c in cases)}</span></div>")
    extras_html = f"<section class='card case-sets'><h2>Cases not compared</h2>{''.join(extras)}</section>" if extras else ""

    if skill_diff:
        lines = []
        for line in skill_diff:
            kind = "add" if line.startswith("+") and not line.startswith("+++") else "remove" if line.startswith("-") and not line.startswith("---") else "meta" if line.startswith(("@@", "+++", "---")) else "context"
            lines.append(f"<div class='diff-line {kind}'><code>{html.escape(line or ' ')}</code></div>")
        skill_html = "<div class='diff-view'>" + "".join(lines) + "</div>"
    else:
        skill_html = "<p class='muted'>No skill diff is available: the captured SKILL.md snapshots are missing or identical.</p>"

    method = (
        "Worker time is wall-clock execution, including tool calls and subagent waits; it excludes setup, evidence capture and grading. "
        "Time change is v2 minus v1; negative means faster. Means include all timed trials, regardless of outcome; missing timings are N/A. "
        "Scores and pass rates are higher-is-better. Values are means across each case and configuration. "
        "Billed output includes reasoning tokens; lower is better for token and cost axes. "
        f"Worker cost excludes semantic judges and is an API-equivalent estimate using public list prices ({PRICING_AS_OF}, {PRICING_SOURCE}), not actual subscription or credit spend."
    )
    title = f"{old_id} → {new_id}"
    return (
        f"<div class='report-heading'><div class='eyebrow'>Offline evaluation comparison</div>"
        f"<h1>{html.escape(skill)}</h1><p>{html.escape(title)}</p></div>"
        f"{warnings_html}{summary_html}{''.join(case_sections)}{extras_html}"
        f"<details class='card disclosure skill-diff'><summary>Skill language change</summary><div class='disclosure-body'>{skill_html}</div></details>"
        f"<details class='card disclosure method-note'><summary>Metric definitions and interpretation</summary><div class='disclosure-body'><p>{html.escape(method)}</p></div></details>"
    )


COMPARISON_STYLE = """
:root { color-scheme:light; --text:#172033; --muted:#5b677d; --border:#dbe3ef; --page:#f6f8fb; --blue:#2563eb; --mono:ui-monospace,SFMono-Regular,Menlo,monospace; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
* { box-sizing:border-box; } body { margin:0; background:var(--page); color:var(--text); line-height:1.5; font-size:15px; }
main { width:min(1180px,calc(100% - 48px)); margin:24px auto 56px; } h1 { font-size:26px; line-height:1.2; margin:4px 0 6px; letter-spacing:-.02em; } h2 { font-size:17px; margin:0; } h3 { font-size:15px; margin:0; } p { margin:0; }
.report-heading { margin-bottom:18px; } .report-heading p,.muted { color:var(--muted); font-size:14px; } .eyebrow,.version-label { color:var(--blue); font-size:12px; font-weight:750; text-transform:uppercase; letter-spacing:.06em; }
.card,.run-panel { background:#fff; border:1px solid var(--border); border-radius:12px; box-shadow:0 3px 12px rgba(25,45,80,.035); } .card { margin-bottom:16px; }
.notice { margin-bottom:16px; padding:14px 18px; border:1px solid #f5d48c; border-left:4px solid #d97706; border-radius:8px; background:#fffbeb; color:#78350f; } .notice strong { display:block; font-size:14px; } .notice p { margin-top:3px; font-size:13px; }
.summary-card { display:flex; justify-content:space-between; align-items:center; gap:18px; flex-wrap:wrap; padding:16px 20px; } .summary-card p { color:var(--muted); font-size:13px; margin-top:4px; } .summary-counts { display:flex; flex-wrap:wrap; gap:10px 22px; color:var(--muted); font-size:14px; } .summary-counts strong { color:var(--text); }
.case-heading { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; margin:22px 0 12px; } .case-name { font:14px var(--mono); overflow-wrap:anywhere; margin:5px 0; } .score-verdict { font-size:13px; font-weight:700; white-space:nowrap; }
.run-panels { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; margin-bottom:16px; } .run-panel { overflow:hidden; border-top:3px solid #9aacc5; } .run-panel.v2 { border-color:#adc8ed; border-top:3px solid var(--blue); box-shadow:0 3px 14px rgba(37,99,235,.09); } .run-header { padding:17px 20px; border-bottom:1px solid var(--border); } .run-panel.v2 .run-header { background:#f2f7ff; } .run-header h3 { margin:4px 0; overflow-wrap:anywhere; } .run-header p { color:var(--muted); font-size:13px; margin-top:3px; } .run-score { display:flex; align-items:baseline; gap:7px; padding:20px 20px 11px; } .run-score strong { font-size:30px; line-height:1; font-variant-numeric:tabular-nums; } .run-score span { color:var(--muted); font-size:14px; } .run-rows { padding:0 20px 10px; } .run-row { display:flex; justify-content:space-between; gap:15px; padding:10px 0; border-bottom:1px solid #edf1f6; font-size:14px; } .run-row:last-child { border:0; } .run-row span { color:var(--muted); } .run-row strong { text-align:right; font-variant-numeric:tabular-nums; }
.changes { padding:18px 20px 5px; } .changes header { margin-bottom:12px; } .changes header p { color:var(--muted); font-size:13px; margin-top:4px; } .change-row { display:grid; grid-template-columns:minmax(140px,1fr) minmax(140px,1fr) minmax(155px,1fr); align-items:center; gap:14px; padding:12px 0; border-top:1px solid var(--border); font-size:14px; } .change-direction { color:var(--muted); font-size:13px; } .change-value { text-align:right; font-variant-numeric:tabular-nums; } .change-value span { display:block; color:var(--muted); font-size:12px; } .good { color:#047857; } .bad { color:#be123c; } .neutral { color:#475569; }
.disclosure { overflow:hidden; } .disclosure > summary { cursor:pointer; padding:15px 20px; color:var(--blue); font-size:14px; font-weight:700; } .disclosure > summary:focus-visible,.trial-records > summary:focus-visible,.source-row a:focus-visible { outline:3px solid #93c5fd; outline-offset:-3px; } .disclosure-body { padding:0 20px 18px; } .disclosure-body p { font-size:14px; color:var(--muted); } .axis-list { overflow-x:auto; border:1px solid var(--border); border-radius:8px; } .axis-row { min-width:650px; display:grid; grid-template-columns:minmax(150px,1.3fr) minmax(80px,.7fr) minmax(80px,.7fr) minmax(145px,1fr) minmax(75px,.5fr); gap:12px; align-items:center; padding:11px 12px; border-bottom:1px solid var(--border); font-size:13px; font-variant-numeric:tabular-nums; } .axis-row:first-child { background:#f6f8fc; } .axis-row:last-child { border-bottom:0; } .axis-row small { color:var(--muted); margin-right:5px; } .delta,.verdict { background:transparent; border:0; border-radius:0; padding:0; font-size:13px; } .verdict { text-transform:none; }
.trial-records { margin-top:14px; border-top:1px solid var(--border); padding-top:12px; } .trial-records summary { cursor:pointer; color:var(--blue); font-weight:650; font-size:14px; } .table-scroll { overflow-x:auto; margin-top:10px; } table { width:100%; min-width:670px; border-collapse:collapse; font-size:13px; font-variant-numeric:tabular-nums; } th,td { padding:9px 10px; text-align:left; border-bottom:1px solid var(--border); } thead th { background:#f6f8fc; color:var(--muted); font-size:12px; } tbody th { font-weight:650; } tbody tr:last-child td,tbody tr:last-child th { border-bottom:0; }
.case-sets { padding:18px 20px; } .case-sets div { display:grid; gap:4px; margin-top:10px; font-size:14px; } .case-sets span { color:var(--muted); overflow-wrap:anywhere; } .diff-view { overflow:auto; margin-top:8px; border:1px solid var(--border); border-radius:8px; font:12px/1.6 var(--mono); } .diff-line { min-width:max-content; padding:3px 12px; white-space:pre; } .diff-line.add { color:#166534; background:#ecfdf5; } .diff-line.remove { color:#9f1239; background:#fff1f2; } .diff-line.meta { color:#4338ca; background:#eef2ff; }
.source-row { display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-top:24px; padding-top:14px; border-top:1px solid var(--border); color:var(--muted); font-size:12px; } .source-row a { color:var(--blue); text-decoration:none; font-weight:650; } .source-row a:hover { text-decoration:underline; }
@media(max-width:760px) { main { width:calc(100% - 24px); margin-top:16px; } .run-panels { grid-template-columns:1fr; } .case-heading { flex-direction:column; gap:6px; } .change-row { grid-template-columns:1fr auto; } .change-direction { grid-row:2; } .change-value { grid-column:2; grid-row:1 / span 2; } }
"""
