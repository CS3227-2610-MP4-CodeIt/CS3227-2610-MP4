"""Check timeline clipping in a real browser, including transition frames."""

import json
from pathlib import Path
import re
import shutil
import subprocess

import pytest

from _lib.usage_html import _SCRIPT, _STYLE, _timeline_component


CHROME = shutil.which("google-chrome") or shutil.which("chromium")
if not CHROME:
    mac_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    CHROME = str(mac_chrome) if mac_chrome.exists() else None


@pytest.mark.skipif(not CHROME, reason="Chrome or Chromium is required for layout checks")
@pytest.mark.parametrize("lanes,width", [(5, 1100), (8, 1100), (5, 1600)])
def test_trace_keeps_every_lane_inside_map_during_open_and_close(tmp_path, lanes, width):
    timeline = _timeline_component({
        "start_ts": "2026-10-28T00:00:00Z",
        "end_ts": "2026-10-28T00:02:00Z",
        "children": [{
            "agent_nickname": f"Reviewer {index}",
            "start_ts": "2026-10-28T00:00:10Z",
            "end_ts": "2026-10-28T00:01:40Z",
            "events": [{"ts": "2026-10-28T00:00:20Z", "kind": "cmd", "command": "inspect",
                        "output": "Recorded output line\n" * 200}],
        } for index in range(lanes - 1)],
    }, "layout")
    probe = r"""
const stage = document.querySelector('.u-stage');
const failures = [];
function check(label) {
  const map = stage.querySelector('.u-map-scroll');
  const clip = map.getBoundingClientRect();
  const trace = stage.querySelector('.u-trace').getBoundingClientRect();
  if (stage.classList.contains('open') && clip.right > trace.left + 1)
    failures.push(label + ': map overlaps trace');
  if (stage.classList.contains('open') && Math.abs(clip.bottom - trace.bottom) > 1)
    failures.push(label + ': trace extends below map viewport');
  stage.querySelectorAll('.u-block').forEach(bar => {
    const rect = bar.getBoundingClientRect();
    if (rect.left < clip.left - 1 || rect.right > clip.left + map.clientWidth + 1)
      failures.push(label + ': clipped bar ' + bar.dataset.actor);
  });
  const heads = [...stage.querySelectorAll('.u-col-head')];
  stage.querySelectorAll('.u-lane').forEach((lane, index) => {
    const bar = lane.getBoundingClientRect();
    const head = heads[index].getBoundingClientRect();
    if (Math.abs(head.left - bar.left) > 1 || Math.abs(head.right - bar.right) > 1)
      failures.push(label + ': header does not align with lane ' + index);
  });
}
function frames(label) {
  stage.getBoundingClientRect();
  const animations = stage.getAnimations({subtree:true});
  if (!animations.length) failures.push(label + ': transition was not exercised');
  animations.forEach(animation => animation.pause());
  [0, .25, .5, .75, 1].forEach(fraction => {
    animations.forEach(animation => {
      animation.currentTime = Number(animation.effect.getTiming().duration) * fraction;
    });
    check(label + ' ' + fraction);
  });
  animations.forEach(animation => animation.finish());
}
check('closed');
openTimelineActor('layout-agent-0');
frames('opening');
check('open');
const mapScroll = stage.querySelector('.u-map-scroll');
const traceScroll = stage.querySelector('.u-trace-agent:not(.hidden) .u-event-list');
mapScroll.scrollTop = mapScroll.scrollHeight;
traceScroll.scrollTop = traceScroll.scrollHeight;
if (mapScroll.scrollTop <= 0 || traceScroll.scrollTop <= 0)
  failures.push('long map and trace must both scroll within their viewports');
check('scrolled to bottom');
openTimelineActor('layout-agent-1');
check('switched actor');
closeTimeline(stage);
frames('closing');
check('closed again');
openTimelineActor('layout-agent-0');
frames('reopening');
check('reopened');
const result = document.createElement('pre');
result.id = 'layout-result';
result.textContent = JSON.stringify(failures);
document.body.append(result);
"""
    page = tmp_path / "timeline.html"
    page.write_text(
        f"<!doctype html><meta charset='utf-8'><style>{_STYLE}</style>"
        f"<div style='width:{width}px'>{timeline}</div>"
        f"<script>{_SCRIPT}</script><script>{probe}</script>", encoding="utf-8"
    )
    result = subprocess.run([
        CHROME, "--headless", "--no-sandbox", "--disable-gpu",
        "--no-first-run", "--disable-background-networking",
        f"--user-data-dir={tmp_path / 'chrome'}", f"--window-size={width + 100},1000",
        "--dump-dom", page.as_uri(),
    ], text=True, capture_output=True, timeout=30, check=True)
    match = re.search(r'<pre id="layout-result">(.*?)</pre>', result.stdout, re.S)
    assert match, result.stderr[-2000:]
    assert json.loads(match.group(1)) == []
