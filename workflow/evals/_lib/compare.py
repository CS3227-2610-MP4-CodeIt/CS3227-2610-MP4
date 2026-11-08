"""Cross-experiment version/regression comparator and Markdown rendering."""

from __future__ import annotations

import argparse
import difflib
import html
import re
from pathlib import Path
from typing import Callable

from _lib.common import SKILL_NAME, _fmt, read_json
from _lib.paths import EVALS_ROOT, trial_directory
from _lib.accounting import observation_tokens
from _lib.comparison_view import COMPARISON_STYLE, render_comparison_body
from _lib.detail_navigation import HEADER_STYLE, header_stats, render_header
from _lib.pricing import (
    LONG_CONTEXT_THRESHOLD,
    PRICING_AS_OF,
    PRICING_SOURCE,
    estimate_api_cost,
    format_cost,
    format_cost_delta,
    format_delta,
)
from _lib.trace import read_skill_snapshot_text
from _lib.timing import format_seconds, time_delta, timing_summary


# --- Layer 2b: cross-experiment version/regression comparator (read-only) ---


def _axis_verdict(old, new, higher_is_better: bool) -> str:
    """Classify a numeric change as improved / regressed / unchanged. Pure."""
    if old is None or new is None:
        return "unknown"
    if new == old:
        return "unchanged"
    better = new > old if higher_is_better else new < old
    return "improved" if better else "regressed"


def _case_representative(experiment: dict, test_case: str, configuration: str) -> dict:
    """Return one per-trial result for a case/config, for reading run.json. Pure."""
    for result in experiment.get("results", []):
        if (
            result.get("test_case") == test_case
            and result.get("configuration") == configuration
        ):
            return result
    return {}


def compare_cell(old_cell: dict, new_cell: dict) -> dict:
    """Diff two cells across score, pass rate, and token axes. Pure.

    Verdict direction: score and pass rate are higher-is-better; every token
    axis is lower-is-better (fewer tokens for equal-or-better score is the win).
    """
    old_score = old_cell.get("mean_score")
    new_score = new_cell.get("mean_score")

    def _pass_rate(cell: dict):
        total = cell.get("total_trials") or 0
        return (cell.get("passed_trials", 0) / total) if total else None

    old_pass = _pass_rate(old_cell)
    new_pass = _pass_rate(new_cell)
    old_tokens = observation_tokens(old_cell.get("mean_tokens") or {})
    new_tokens = observation_tokens(new_cell.get("mean_tokens") or {})

    result = {
        "n_old": old_cell.get("total_trials", 0),
        "n_new": new_cell.get("total_trials", 0),
        "passed_old": old_cell.get("passed_trials", 0),
        "passed_new": new_cell.get("passed_trials", 0),
        "timed_old": old_cell.get("timed_trials", 0),
        "timed_new": new_cell.get("timed_trials", 0),
        "worker_time": {
            "old": old_cell.get("mean_worker_seconds"),
            "new": new_cell.get("mean_worker_seconds"),
            "verdict": _axis_verdict(
                old_cell.get("mean_worker_seconds"),
                new_cell.get("mean_worker_seconds"), higher_is_better=False,
            ),
        },
        "score": {
            "old": old_score,
            "new": new_score,
            "verdict": _axis_verdict(old_score, new_score, higher_is_better=True),
        },
        "pass_rate": {
            "old": old_pass,
            "new": new_pass,
            "verdict": _axis_verdict(old_pass, new_pass, higher_is_better=True),
        },
    }
    for key, cell_field in (
        ("deterministic_score", "mean_deterministic_score"),
        ("semantic_score", "mean_semantic_score"),
    ):
        old_val = old_cell.get(cell_field)
        new_val = new_cell.get(cell_field)
        if old_val is not None or new_val is not None:
            result[key] = {
                "old": old_val,
                "new": new_val,
                "verdict": _axis_verdict(old_val, new_val, higher_is_better=True),
            }
    # Token axes that reflect a skill-wording change: uncached input (a shorter
    # skill means less context every turn), output, reasoning, and billed total.
    for axis in (
        "uncached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "billed_output_tokens",
    ):
        old_value = old_tokens.get(axis)
        new_value = new_tokens.get(axis)
        result[axis] = {
            "old": old_value,
            "new": new_value,
            "verdict": _axis_verdict(old_value, new_value, higher_is_better=False),
        }
    # Carry the raw mean-token dicts so a caller that knows the model can derive
    # an API-equivalent cost estimate without recomputing per-axis values.
    result["_cost_old"] = old_cell.get("mean_est_cost")
    result["_cost_new"] = new_cell.get("mean_est_cost")
    result["_mean_tokens_old"] = old_tokens
    result["_mean_tokens_new"] = new_tokens
    return result


def partition_cases(old_cases: list[str], new_cases: list[str]) -> dict:
    """Split case names into both / only-old / only-new. Pure."""
    old_set, new_set = set(old_cases), set(new_cases)
    return {
        "both": sorted(old_set & new_set),
        "only_old": sorted(old_set - new_set),
        "only_new": sorted(new_set - old_set),
    }


def _cell(experiment: dict, test_case: str, configuration: str) -> dict:
    raw = (
        experiment.get("aggregates", {})
        .get("cells", {})
        .get(test_case, {})
        .get(configuration, {})
    )
    if not raw:
        return {}
    cell = dict(raw)
    if "timed_trials" not in cell:
        cell.update(timing_summary([
            r for r in experiment.get("results", [])
            if r.get("test_case") == test_case
            and r.get("configuration") == configuration
        ]))
    if "mean_deterministic_score" not in cell and experiment.get("results"):
        trials = [
            r
            for r in experiment.get("results", [])
            if r.get("test_case") == test_case
            and r.get("configuration") == configuration
        ]
        det_scores = [
            r["deterministic_score"]
            for r in trials
            if isinstance(r.get("deterministic_score"), (int, float))
        ]
        sem_scores = [
            r["semantic_score"]
            for r in trials
            if isinstance(r.get("semantic_score"), (int, float))
        ]
        cell["mean_deterministic_score"] = (
            round(sum(det_scores) / len(det_scores), 2) if det_scores else None
        )
        cell["mean_semantic_score"] = (
            round(sum(sem_scores) / len(sem_scores), 2) if sem_scores else None
        )
    return cell


def _historical_worker_cost(
    experiment: dict, test_case: str, configuration: str
) -> float | None:
    """Reconstruct an API-equivalent worker cost when an old cell omitted it.

    Prefer complete per-request accounting. For older manifests that retained
    only per-trial token totals, price them only when the model is known, there
    are no separately-modelled subagent tokens, and each trial's total input is
    below the long-context threshold. In that case every constituent request
    must use the short-context tier, so additive token totals preserve cost.
    """
    results = [
        result for result in experiment.get("results", [])
        if result.get("test_case") == test_case
        and result.get("configuration") == configuration
    ]
    if not results:
        return None
    costs: list[float] = []
    for result in results:
        accounting = result.get("worker_accounting") or result.get("accounting")
        coverage = accounting.get("coverage") if isinstance(accounting, dict) else None
        if isinstance(coverage, dict):
            if coverage.get("status") != "complete":
                return None
            cost = accounting.get("known_cost", accounting.get("est_cost"))
            if cost is None:
                return None
            costs.append(float(cost))
            continue

        raw_tokens = result.get("tokens")
        model = result.get("resolved_model") or result.get("model")
        if not isinstance(raw_tokens, dict) or not model:
            return None
        subagent_tokens = observation_tokens(result.get("subagent_tokens") or {})
        if any(float(value or 0) for value in subagent_tokens.values()):
            return None
        tokens = observation_tokens(raw_tokens)
        if int(tokens.get("input_tokens") or 0) >= LONG_CONTEXT_THRESHOLD:
            return None
        cost = estimate_api_cost(tokens, model)
        if cost is None:
            return None
        costs.append(float(cost))
    if len(costs) != len(results):
        return None
    return round(sum(costs) / len(costs), 6)


def _confounds(old_rep: dict, new_rep: dict) -> list[str]:
    """Detect model/fixture confounds for one case by reading its run.json."""
    warnings: list[str] = []
    old_model = old_rep.get("resolved_model")
    new_model = new_rep.get("resolved_model")
    if old_model and new_model and old_model != new_model:
        warnings.append(f"model changed ({old_model} -> {new_model})")
    old_fixture = _run_field(old_rep, "fixture_sha256")
    new_fixture = _run_field(new_rep, "fixture_sha256")
    if old_fixture and new_fixture and old_fixture != new_fixture:
        warnings.append("fixture changed")
    old_profiles = _run_field(old_rep, "agent_profile_sha256") or {}
    new_profiles = _run_field(new_rep, "agent_profile_sha256") or {}
    if old_profiles != new_profiles:
        warnings.append("agent profiles changed")
    return warnings


def _run_field(result: dict, field: str):
    """Read a field from a trial's run.json via its run_directory. READ-ONLY."""
    run_directory = trial_directory(result)
    if run_directory is None:
        return None
    metadata = read_json(run_directory / "run.json") or {}
    return metadata.get(field)


def _skill_diff(old_rep: dict, new_rep: dict) -> list[str]:
    """Unified diff of the two experiments' captured SKILL.md snapshots."""
    old_dir = trial_directory(old_rep)
    new_dir = trial_directory(new_rep)
    if old_dir is None or new_dir is None:
        return []
    old_meta = read_json(old_dir / "run.json") or {}
    new_meta = read_json(new_dir / "run.json") or {}
    old_text = read_skill_snapshot_text(old_dir, old_meta)
    new_text = read_skill_snapshot_text(new_dir, new_meta)
    if old_text is None or new_text is None or old_text == new_text:
        return []
    return list(
        difflib.unified_diff(
            old_text.splitlines(),
            new_text.splitlines(),
            fromfile="v1/SKILL.md",
            tofile="v2/SKILL.md",
            lineterm="",
        )
    )


def render_comparison_markdown(
    skill: str, old_id: str, new_id: str, partition: dict, rows: list[dict],
    skill_diff: list[str], summary: dict, provenance: dict,
) -> str:
    """Build the markdown comparison report. Pure (no I/O)."""
    trials = provenance.get("trials") or {}
    old_trials = trials.get("old")
    new_trials = trials.get("new")
    old_model = provenance.get("old_model") or "not captured"
    new_model = provenance.get("new_model") or "not captured"
    old_effort = provenance.get("old_effort") or "not captured"
    new_effort = provenance.get("new_effort") or "not captured"
    config = provenance.get("config") or "with-skill"
    models_match = (
        provenance.get("old_model")
        and provenance.get("new_model")
        and provenance["old_model"] == provenance["new_model"]
        and provenance.get("old_effort") == provenance.get("new_effort")
    )
    title_suffix = f" ({config})" if config != "with-skill" else ""
    lines = [
        f"# Comparison: {skill}{title_suffix} — {old_id} (v1) vs {new_id} (v2)",
        "",
        "| Setup | v1 (" + old_id + ") | v2 (" + new_id + ") |",
        "|---|---|---|",
        f"| Model | {old_model} | {new_model} |",
        f"| Reasoning effort | {old_effort} | {new_effort} |",
        f"| Trials per cell | {old_trials if old_trials is not None else '?'} "
        f"| {new_trials if new_trials is not None else '?'} |",
    ]
    if config != "with-skill":
        lines.append(f"| Configuration | {config} | {config} |")
    lines.append("")
    if not models_match:
        lines.append(
            "> WARNING: model and/or reasoning effort differ between the two "
            "experiments. Score and especially token comparisons may be "
            "confounded by the model change rather than the skill edit."
        )
        lines.append("")
    lines.extend([
        "| Summary | Value |",
        "|---|---|",
        f"| Shared cases | {len(partition['both'])} |",
        f"| Improved (score) | {summary['improved']} |",
        f"| Regressed (score) | {summary['regressed']} |",
        f"| Unchanged (score) | {summary['unchanged']} |",
    ])
    if summary.get("unknown", 0):
        lines.append(f"| Unknown (score) | {summary['unknown']} |")
    if partition["only_old"]:
        lines.append(f"| Dropped in v2 (not compared) | {', '.join(partition['only_old'])} |")
    if partition["only_new"]:
        lines.append(f"| Added in v2 (not compared) | {', '.join(partition['only_new'])} |")
    lines.append("")
    if partition["only_old"] or partition["only_new"]:
        lines.append("> WARNING: test-case sets differ; aggregate comparison is weakened.")
        lines.append("")

    if rows:
        lines.append("## Case overview")
        lines.append("")
        lines.append(
            "| Test case | Score (v1 -> v2) | Pass rate | Mean worker time (v1 -> v2) | Time change | Billed out (v1 -> v2) "
            "| Est. cost (v1 -> v2) | Score verdict |"
        )
        lines.append("|---|---|---|---|---|---|---|---|")
        for row in rows:
            diff = row["diff"]
            sc = diff.get("score", {})
            sc_text = f"{_fmt(sc.get('old'))} -> {_fmt(sc.get('new'))}"
            if sc.get("old") is not None and sc.get("new") is not None and sc["old"] != sc["new"]:
                sc_text += f" ({sc['new'] - sc['old']:+g})"
            n_old = diff.get("n_old", 0)
            n_new = diff.get("n_new", 0)
            p_old = diff.get("passed_old")
            p_new = diff.get("passed_new")
            if p_old is not None and p_new is not None and n_old and n_new:
                pr_text = f"{p_old}/{n_old} -> {p_new}/{n_new}"
            else:
                pr = diff.get("pass_rate", {})
                pr_text = f"{_fmt(pr.get('old'))} -> {_fmt(pr.get('new'))}"
            bo = diff.get("billed_output_tokens", {})
            bo_text = f"{_fmt(bo.get('old'))} -> {_fmt(bo.get('new'))}"
            if bo.get("old") and bo.get("new") is not None:
                pct = (bo["new"] - bo["old"]) / bo["old"] * 100
                bo_text += f" ({pct:+.1f}%)"
            c_old = diff.get("_cost_old")
            c_new = diff.get("_cost_new")
            if c_old is not None and c_new is not None:
                cost_text = f"{format_cost(c_old)} -> {format_cost(c_new)}"
                if c_old:
                    cost_text += f" ({(c_new - c_old) / c_old * 100:+.1f}%)"
            else:
                cost_text = "n/a"
            lines.append(
                f"| {row['test_case']} | {sc_text} | {pr_text} | "
                f"{format_seconds(diff.get('worker_time', {}).get('old'))} -> "
                f"{format_seconds(diff.get('worker_time', {}).get('new'))} | "
                f"{time_delta(diff.get('worker_time', {}).get('old'), diff.get('worker_time', {}).get('new'))} | {bo_text} "
                f"| {cost_text} | {sc.get('verdict', 'n/a')} |"
            )
        lines.append("")

    AXES = [
        ("score", "score"),
        ("deterministic_score", "det score"),
        ("semantic_score", "sem score"),
        ("pass_rate", "pass rate"),
        ("uncached_input_tokens", "uncached input"),
        ("output_tokens", "output"),
        ("reasoning_output_tokens", "reasoning"),
        ("billed_output_tokens", "billed output"),
    ]
    for row in rows:
        diff = row["diff"]
        n_old = diff.get("n_old", "?")
        n_new = diff.get("n_new", "?")
        lines.append(
            f"## {row['test_case']}  (mean of n={n_old} v1 trial(s) -> "
            f"n={n_new} v2 trial(s))"
        )
        lines.append("")
        lines.append("| Axis | v1 | v2 | Change | Verdict |")
        lines.append("|---|---|---|---|---|")
        timing = diff.get("worker_time", {})
        lines.append(
            f"| mean worker time | {format_seconds(timing.get('old'))} | "
            f"{format_seconds(timing.get('new'))} | "
            f"{time_delta(timing.get('old'), timing.get('new'))} | "
            f"{timing.get('verdict', 'unknown')} |"
        )
        lines.append(
            f"| timed trials / total | {diff.get('timed_old', 0)}/{n_old} | "
            f"{diff.get('timed_new', 0)}/{n_new} | — | — |"
        )
        for key, label in AXES:
            a = diff.get(key)
            if not a:
                continue
            lines.append(
                f"| {label} | {_fmt(a['old'])} | {_fmt(a['new'])} | "
                f"{format_delta(a['old'], a['new'])} | {a['verdict']} |"
            )
        cost_old = diff.get("_cost_old")
        cost_new = diff.get("_cost_new")
        if cost_old is not None and cost_new is not None:
            cost_verdict = _axis_verdict(cost_old, cost_new, higher_is_better=False)
        else:
            cost_verdict = "n/a"
        lines.append(
            f"| est. API-equiv. cost | {format_cost(cost_old)} | "
            f"{format_cost(cost_new)} | {format_cost_delta(cost_old, cost_new)} | "
            f"{cost_verdict} |"
        )
        lines.append("")
        if row["confounds"]:
            lines.append(
                f"> CONFOUNDED: {'; '.join(row['confounds'])} "
                "(hold everything but the skill constant)."
            )
            lines.append("")

    lines.append("## Skill language change (v1 -> v2)")
    lines.append("")
    if skill_diff:
        lines.append("```diff")
        lines.extend(skill_diff)
        lines.append("```")
    else:
        lines.append("_No skill-language diff available "
                     "(snapshots missing or identical)._")
    lines.append("")
    lines.append(
        "_Worker time is wall-clock execution, including tool calls and subagent waits; "
        "excludes setup, subsequent evidence capture and grading. Time change = v2 − v1; "
        "negative means faster. Means include all timed trials, regardless of outcome; "
        "missing timings are N/A._"
    )
    lines.append("")
    lines.append(
        f"_Every per-case number is a MEAN over that cell's trials; "
        f"`billed output` = output (including reasoning) (lower is better on token/cost axes); "
        f"`est. API-equiv. cost` is an estimate at public API list prices "
        f"({PRICING_AS_OF}, {PRICING_SOURCE}) — NOT actual subscription or credit spend._"
    )
    lines.append("")
    return "\n".join(lines)


def _verdict_class(value: str) -> str:
    value = value.lower()
    return "good" if value in {"improved", "pass", "passed"} else "bad" if value in {"regressed", "fail", "failed"} else "neutral"


def _html_number(value, *, digits: int = 2) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        rendered = f"{value:,.{digits}f}".rstrip("0").rstrip(".")
        return rendered
    return str(value)


def _html_delta(old, new, *, lower_is_better: bool = False) -> str:
    if old is None or new is None:
        return "Change unavailable"
    delta = new - old
    if delta == 0:
        return "No change"
    percent = f" ({delta / old * 100:+.1f}%)" if old else ""
    unit = ""
    return f"{delta:+,.2f}".rstrip("0").rstrip(".") + unit + percent


def _render_case_details(row: dict) -> str:
    diff = row["diff"]
    axes = [
        ("Worker time", diff.get("worker_time", {}).get("old"), diff.get("worker_time", {}).get("new"), diff.get("worker_time", {}).get("verdict"), "time"),
        ("Score", diff.get("score", {}).get("old"), diff.get("score", {}).get("new"), diff.get("score", {}).get("verdict"), "number"),
        ("Deterministic score", diff.get("deterministic_score", {}).get("old"), diff.get("deterministic_score", {}).get("new"), diff.get("deterministic_score", {}).get("verdict"), "number"),
        ("Semantic score", diff.get("semantic_score", {}).get("old"), diff.get("semantic_score", {}).get("new"), diff.get("semantic_score", {}).get("verdict"), "number"),
        ("Pass rate", diff.get("pass_rate", {}).get("old"), diff.get("pass_rate", {}).get("new"), diff.get("pass_rate", {}).get("verdict"), "percent"),
        ("Uncached input", diff.get("uncached_input_tokens", {}).get("old"), diff.get("uncached_input_tokens", {}).get("new"), diff.get("uncached_input_tokens", {}).get("verdict"), "number"),
        ("Output", diff.get("output_tokens", {}).get("old"), diff.get("output_tokens", {}).get("new"), diff.get("output_tokens", {}).get("verdict"), "number"),
        ("Reasoning", diff.get("reasoning_output_tokens", {}).get("old"), diff.get("reasoning_output_tokens", {}).get("new"), diff.get("reasoning_output_tokens", {}).get("verdict"), "number"),
        ("Billed output", diff.get("billed_output_tokens", {}).get("old"), diff.get("billed_output_tokens", {}).get("new"), diff.get("billed_output_tokens", {}).get("verdict"), "number"),
        ("Estimated API-equivalent cost", diff.get("_cost_old"), diff.get("_cost_new"), _axis_verdict(diff.get("_cost_old"), diff.get("_cost_new"), False), "cost"),
    ]
    rows_html = []
    for label, old, new, verdict, kind in axes:
        if old is None and new is None and label not in {"Worker time", "Estimated API-equivalent cost"}:
            continue
        if kind == "time":
            old_text, new_text = format_seconds(old), format_seconds(new)
            delta = time_delta(old, new)
        elif kind == "cost":
            old_text, new_text = format_cost(old), format_cost(new)
            delta = format_cost_delta(old, new)
        elif kind == "percent":
            old_text, new_text = (f"{old*100:.1f}%" if old is not None else "N/A"), (f"{new*100:.1f}%" if new is not None else "N/A")
            delta = _html_delta(old, new)
        else:
            old_text, new_text = _html_number(old), _html_number(new)
            delta = format_delta(old, new)
        rows_html.append(
            f"<tr><th scope='row'>{html.escape(label)}</th>"
            f"<td>{html.escape(old_text)}</td><td>{html.escape(new_text)}</td>"
            f"<td class='{_verdict_class(verdict or 'unknown')}'>{html.escape(delta)}</td>"
            f"<td>{html.escape(verdict or 'unknown')}</td></tr>"
        )
        if label == "Worker time":
            rows_html.append(
                f"<tr><th scope='row'>Timed trials / total</th>"
                f"<td>{html.escape(str(diff.get('timed_old', 0)))}/{html.escape(str(diff.get('n_old', 0)))}</td>"
                f"<td>{html.escape(str(diff.get('timed_new', 0)))}/{html.escape(str(diff.get('n_new', 0)))}</td>"
                "<td>—</td><td>—</td></tr>"
            )
    trial_rows = []
    for version, trials in (("v1", row.get("old_trials", [])), ("v2", row.get("new_trials", []))):
        for trial in trials:
            tokens = observation_tokens(trial.get("tokens") or {})
            trial_rows.append(
                "<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in (
                    version, trial.get("trial", "—"), _html_number(trial.get("score")),
                    "pass" if trial.get("overall_pass") else "fail" if trial.get("overall_pass") is False else "—",
                    format_seconds(trial.get("worker_elapsed_seconds")), _html_number(tokens.get("uncached_input_tokens")),
                    _html_number(tokens.get("billed_output_tokens")),
                )) + "</tr>"
            )
    trial_table = ""
    if trial_rows:
        trial_table = (
            f"<details class='trial-records'><summary>Individual trial records ({len(trial_rows)})</summary>"
            f"<div class='table-scroll'><table><thead><tr><th>Version</th><th>Trial</th><th>Score</th><th>Outcome</th><th>Worker time</th><th>Uncached input</th><th>Billed output</th></tr></thead><tbody>{''.join(trial_rows)}</tbody></table></div></details>"
        )
    table = (
        "<div class='table-scroll'><table class='metric-table'><thead><tr>"
        "<th>Metric</th><th>v1</th><th>v2</th><th>Change</th><th>Verdict</th>"
        f"</tr></thead><tbody>{''.join(rows_html)}</tbody></table></div>"
    )
    return table + trial_table


def render_comparison_html(
    skill: str, markdown_name: str, *,
    old_id: str, new_id: str, partition: dict, rows: list[dict],
    skill_diff: list[str], summary: dict, provenance: dict,
    usage_summary: dict | None = None,
) -> str:
    """Build the HTML view directly from collected comparison data."""
    summary_data = {
        "shared": len(partition.get("both", [])),
        "improved": summary.get("improved", 0),
        "regressed": summary.get("regressed", 0),
        "unchanged": summary.get("unchanged", 0),
        "unknown": summary.get("unknown", 0),
    }
    body = render_comparison_body(
        skill, old_id, new_id, partition, rows, skill_diff, summary_data,
        provenance, _render_case_details,
    )
    online_stats, offline_stats = header_stats(usage_summary)
    project_name = (usage_summary or {}).get("project_name") or EVALS_ROOT.parents[1].name
    header = render_header(
        project_name, online_stats, offline_stats,
        dashboard_href="../../_usage/report.html",
        comparison_label=f"{skill} comparison",
        comparison_title=f"{skill}: {old_id} → {new_id}",
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(skill)}: {html.escape(old_id)} vs {html.escape(new_id)}</title>
  <style>
{COMPARISON_STYLE}
{HEADER_STYLE}
  </style>
</head>
<body>
  {header}
  <main><a class="page-back" href="../../_usage/report.html#offline-comparisons">← Offline eval</a>{body}
    <footer class="source-row"><span>Generated by the local evaluation harness. Cost figures are API-equivalent estimates, not subscription charges.</span><a class="source-link" href="{html.escape(markdown_name, quote=True)}">Markdown source ↗</a></footer>
  </main>
  <script src="../../_usage/header-data.js"></script>
  <script>
    if (window.__EVAL_HEADER_STATS__) {{
      document.querySelectorAll('[data-usage-stat]').forEach(function (element) {{
        var value = window.__EVAL_HEADER_STATS__[element.dataset.usageStat];
        if (typeof value === 'string') element.textContent = value;
      }});
    }}
  </script>
</body>
</html>
"""


def compare_experiments(
    args: argparse.Namespace,
    skills: dict[str, Path],
    fail_fn: Callable[[str], None] | None = None,
) -> int:
    def _fail(msg: str) -> None:
        if fail_fn is not None:
            fail_fn(msg)
        raise SystemExit(1)

    if args.skill in skills:
        skill_root = skills[args.skill]
    elif SKILL_NAME.fullmatch(args.skill):
        # Historical imports may have runs but no currently installed skill or
        # runnable test cases. The read-only comparator can still compare their
        # persisted experiment manifests without invoking an agent.
        skill_root = EVALS_ROOT / args.skill
        if not (skill_root / "runs").is_dir():
            _fail(f"no evaluation runs for {args.skill}; available: {', '.join(skills) or 'none'}")
    else:
        _fail(f"invalid skill name: {args.skill}")
    config = getattr(args, "config", "with-skill") or "with-skill"
    runs_root = skill_root / "runs"
    old_path = runs_root / args.old / "experiment.json"
    new_path = runs_root / args.new / "experiment.json"
    old = read_json(old_path)
    new = read_json(new_path)
    if not isinstance(old, dict):
        _fail(f"cannot read experiment manifest: {old_path}")
    if not isinstance(new, dict):
        _fail(f"cannot read experiment manifest: {new_path}")

    partition = partition_cases(old.get("test_cases", []), new.get("test_cases", []))
    if not partition["both"]:
        print(f"Comparing {args.skill}: {args.old} -> {args.new}")
        print("No shared test cases to compare.")
        return 1

    missing_config = [
        tc for tc in partition["both"]
        if not _cell(old, tc, config) or not _cell(new, tc, config)
    ]
    if len(missing_config) == len(partition["both"]):
        _fail(
            f"configuration '{config}' is missing in one or both experiments "
            f"({args.old}, {args.new})"
        )

    improved = regressed = unchanged = unknown = 0
    rows: list[dict] = []
    for test_case in partition["both"]:
        old_cell = _cell(old, test_case, config)
        new_cell = _cell(new, test_case, config)
        if not old_cell or not new_cell:
            continue
        diff = compare_cell(old_cell, new_cell)
        if diff.get("_cost_old") is None:
            diff["_cost_old"] = _historical_worker_cost(old, test_case, config)
        if diff.get("_cost_new") is None:
            diff["_cost_new"] = _historical_worker_cost(new, test_case, config)
        old_rep = _case_representative(old, test_case, config)
        new_rep = _case_representative(new, test_case, config)
        confounds = _confounds(old_rep, new_rep)
        rows.append({
            "test_case": test_case,
            "diff": diff,
            "confounds": confounds,
            "old_trials": [
                r for r in old.get("results", [])
                if r.get("test_case") == test_case and r.get("configuration") == config
            ],
            "new_trials": [
                r for r in new.get("results", [])
                if r.get("test_case") == test_case and r.get("configuration") == config
            ],
        })
        if diff["score"]["verdict"] == "improved":
            improved += 1
        elif diff["score"]["verdict"] == "regressed":
            regressed += 1
        elif diff["score"]["verdict"] == "unchanged":
            unchanged += 1
        else:
            unknown += 1

    first_case = rows[0]["test_case"]
    skill_diff = (
        _skill_diff(
            _case_representative(old, first_case, "with-skill"),
            _case_representative(new, first_case, "with-skill"),
        )
        if config == "with-skill"
        else []
    )

    # Provenance for the comparability caveat: model + reasoning effort actually
    # resolved, read from a representative trial of each experiment, plus trials
    # per cell. Token/score comparisons are only valid on the same model/effort.
    old_rep0 = _case_representative(old, first_case, config)
    new_rep0 = _case_representative(new, first_case, config)
    provenance = {
        "old_model": old_rep0.get("resolved_model"),
        "new_model": new_rep0.get("resolved_model"),
        "old_effort": old_rep0.get("resolved_reasoning_effort"),
        "new_effort": new_rep0.get("resolved_reasoning_effort"),
        "trials": {"old": old.get("trials"), "new": new.get("trials")},
        "config": config,
    }

    # Write the full report to a comparisons/ dir that is a sibling of runs/, so
    # comparison artifacts never mutate an immutable experiment dir.
    summary = {"improved": improved, "regressed": regressed, "unchanged": unchanged, "unknown": unknown}
    markdown = render_comparison_markdown(
        args.skill, args.old, args.new, partition, rows, skill_diff, summary,
        provenance,
    )
    comparisons_root = skill_root / "comparisons"
    comparisons_root.mkdir(parents=True, exist_ok=True)
    suffix = "-baseline" if config == "baseline" else ""
    out_path = comparisons_root / f"{args.old}-vs-{args.new}{suffix}.md"
    out_path.write_text(markdown, encoding="utf-8")
    html_path = out_path.with_suffix(".html")
    html_path.write_text(
        render_comparison_html(
            args.skill, out_path.name,
            old_id=args.old,
            new_id=args.new,
            partition=partition,
            rows=rows,
            skill_diff=skill_diff,
            summary=summary,
            provenance=provenance,
            usage_summary=read_json(skill_root.parent / "_usage" / "summary.json"),
        ),
        encoding="utf-8",
    )

    # Terminal stays short: the detail lives in the file.
    cfg_label = f" ({config})" if config != "with-skill" else ""
    print(f"Comparing {args.skill}{cfg_label}: {args.old} (v1) -> {args.new} (v2)")
    print(
        f"  {len(rows)} shared case(s): "
        f"{improved} improved, {regressed} regressed, {unchanged} unchanged"
        f"{f', {unknown} unknown' if unknown else ''} (by score)"
    )
    if partition["only_old"] or partition["only_new"]:
        print(
            f"  Note: test-case sets differ "
            f"(+{len(partition['only_new'])} new, -{len(partition['only_old'])} dropped); "
            "not compared."
        )
    confounded = [r["test_case"] for r in rows if r["confounds"]]
    if confounded:
        print(f"  Confounded (model/fixture changed): {', '.join(confounded)}")
    print(f"Report: {out_path}")
    print(f"HTML report: {html_path}")
    return 0
