"""Shared, single-row header and breadcrumb styling for evaluation reports."""

from __future__ import annotations

import html
from typing import Any

from _lib.pricing import format_cost


def _cost_primary(totals: dict[str, Any]) -> str:
    coverage = totals.get("coverage") or {}
    value = totals.get("known_cost") if coverage.get("status") in ("partial", "unavailable") else totals.get("est_cost")
    return format_cost(value) if value is not None else "n/a"


def header_stats(summary: dict[str, Any] | None) -> tuple[str, str]:
    """Format the same aggregate figures used by the usage dashboard."""
    if not isinstance(summary, dict) or not isinstance(summary.get("totals"), dict):
        return "—", "—"
    totals = summary["totals"]
    harness = summary.get("harness_evals") or {}
    eval_totals = harness.get("totals") or {}
    sessions = harness.get("sessions") or []
    experiments = len({(s.get("eval_skill"), s.get("experiment")) for s in sessions})
    return (
        f"{_cost_primary(totals)} · {totals.get('session_count', 0)} sessions",
        f"{_cost_primary(eval_totals)} · {experiments} exps · {eval_totals.get('worker_session_count', 0)} trials",
    )


def render_header(
    project_name: str, online_stats: str, offline_stats: str, *, updated: str = "",
    dashboard_href: str | None = None, comparison_label: str | None = None,
    comparison_title: str | None = None,
) -> str:
    """Render the same header for the dashboard and standalone comparisons."""
    standalone = dashboard_href is not None
    if standalone:
        base = html.escape(dashboard_href, quote=True)
        online = f'<a class="mode-tab" id="tab-real" href="{base}#online">Online eval'
        offline = f'<a class="mode-tab active" id="tab-eval" href="{base}#offline-comparisons" aria-current="location">Offline eval'
        close = "</a>"
        crumbs = (
            '<nav class="header-breadcrumbs" id="header-breadcrumbs" aria-label="Breadcrumb">'
            f'<ol><li><span aria-current="page" title="{html.escape(comparison_title or comparison_label or "Comparison", quote=True)}">'
            f'{html.escape(comparison_label or "Comparison")}</span></li></ol></nav>'
        )
    else:
        online = '<button class="mode-tab active" id="tab-real" aria-pressed="true" onclick="switchMode(\'real\')">Online eval'
        offline = '<button class="mode-tab" id="tab-eval" aria-pressed="false" onclick="switchMode(\'eval\')">Offline eval'
        close = "</button>"
        crumbs = '<nav class="header-breadcrumbs" id="header-breadcrumbs" aria-label="Breadcrumb" hidden></nav>'
    cls = "topbar has-breadcrumb" if standalone else "topbar"
    return (
        f'<header class="{cls}" id="report-header"><div class="brand">'
        '<span class="brand-title"><span class="brand-title-full">Codex Zero-Token Telemetry</span>'
        '<span class="brand-title-short">Telemetry</span></span>'
        f'<span class="repo-badge">{html.escape(project_name)}</span></div>'
        '<nav class="mode-tabs" aria-label="Evaluation mode">'
        f'{online} <span class="tab-pill" data-usage-stat="online">{html.escape(online_stats)}</span>{close}'
        f'{offline} <span class="tab-pill" data-usage-stat="offline">{html.escape(offline_stats)}</span>{close}'
        f'</nav>{crumbs}<div class="updated">{html.escape(updated)}</div></header>'
    )


HEADER_STYLE = """
:root { --app-header-height:64px; }
.topbar { position:sticky; top:0; z-index:50; box-sizing:border-box; display:flex; flex-wrap:nowrap;
  align-items:center; gap:14px; height:var(--app-header-height); padding:8px 20px;
  background:#fff; border-bottom:1px solid #dbe3ef; }
.brand { display:flex; align-items:center; gap:8px; flex:none; min-width:0; }
.brand-title { color:#172033; font-size:15px; font-weight:700; white-space:nowrap; }
.brand-title-short { display:none; }
.repo-badge { max-width:180px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
  font:11px ui-monospace,SFMono-Regular,Menlo,monospace; background:#eef4fb;
  border:1px solid #dbe3ef; border-radius:6px; padding:2px 8px; color:#5b677d; }
.mode-tabs { display:flex; flex:none; align-items:center; gap:4px; }
.mode-tab { display:flex; align-items:center; gap:7px; border:1px solid transparent; border-radius:8px;
  padding:7px 10px; background:transparent; color:#5b677d; cursor:pointer;
  font:600 13px/1.4 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; text-decoration:none; white-space:nowrap; }
.mode-tab.active { background:#eef4fb; color:#2563eb; border-color:#bfdbfe; }
.tab-pill { font:600 11px ui-monospace,SFMono-Regular,Menlo,monospace; background:#fff;
  border:1px solid #dbe3ef; border-radius:999px; padding:2px 7px; color:#5b677d; }
.header-breadcrumbs { flex:1 1 0; min-width:0; overflow:hidden; }
.header-breadcrumbs[hidden] { display:none !important; }
.header-breadcrumbs ol { display:flex; align-items:center; min-width:0; gap:7px; margin:0; padding:0; list-style:none; }
.header-breadcrumbs ol::before,.header-breadcrumbs li + li::before { content:'›'; flex:none; color:#94a3b8; font-size:17px; }
.header-breadcrumbs li { display:flex; align-items:center; gap:7px; min-width:0; max-width:300px; flex:0 1 auto; }
.header-breadcrumbs li > button,.header-breadcrumbs li > a,.header-breadcrumbs li > span { display:block; min-width:0;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#2563eb; text-decoration:none;
  border:0; background:transparent; padding:8px 0; font:600 13px/1.4 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
.header-breadcrumbs li > button { cursor:pointer; text-align:left; }
.header-breadcrumbs li > button:hover,.header-breadcrumbs li > a:hover { text-decoration:underline; }
.header-breadcrumbs li > span[aria-current] { color:#5b677d; font-weight:600; }
.topbar button:focus-visible,.topbar a:focus-visible { outline:2px solid #2563eb; outline-offset:2px; border-radius:3px; }
.page-back { display:inline-block; max-width:100%; margin:0 0 12px; padding:0; border:0;
  background:transparent; color:#2563eb; cursor:pointer; text-align:left; text-decoration:none;
  overflow-wrap:anywhere; font:600 13px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
.page-back:hover { color:#1d4ed8; text-decoration:underline; }
.page-back:focus-visible { outline:2px solid #2563eb; outline-offset:3px; border-radius:3px; }
.updated { margin-left:auto; flex:none; color:#5b677d; font:12px ui-monospace,SFMono-Regular,Menlo,monospace; }
.topbar.has-breadcrumb .updated { display:none; }
@media(max-width:1250px) { .topbar.has-breadcrumb .repo-badge,.topbar.has-breadcrumb .tab-pill { display:none; } }
@media(max-width:760px) { .topbar { gap:6px; padding:8px 10px; } .repo-badge,.tab-pill,.updated { display:none; }
  .brand-title-full { display:none; } .brand-title-short { display:inline; } .brand-title { font-size:13px; }
  .mode-tabs { gap:0; } .mode-tab { padding:8px 5px; font-size:12px; } .header-breadcrumbs ol,.header-breadcrumbs li { gap:4px; }
  .header-breadcrumbs li > button,.header-breadcrumbs li > a,.header-breadcrumbs li > span { font-size:12px; } }
"""
