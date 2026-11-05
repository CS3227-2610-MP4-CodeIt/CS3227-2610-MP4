"""Regression coverage for deterministic online usage observations."""

import json
import re
from html.parser import HTMLParser

from _lib.usage import (
    _inject_captured_subagents,
    _online_session_observations,
    _rollout_inspection,
    parse_session_rollout,
)
from _lib.usage_html import _real_session_details


def _finding_map(findings):
    return {finding["kind"]: finding for finding in findings}


def test_command_observations_are_evidence_linked_and_deterministic():
    events = [
        {"kind": "cmd", "command": "make check", "exit_code": 2, "ts": "2026-10-28T10:00:01Z", "event_index": 4},
        {"kind": "cmd", "command": "make check", "exit_code": 0, "ts": "2026-10-28T10:00:03Z", "event_index": 7},
    ]

    first = _online_session_observations("root-123", events, 0, True, "completed", [])
    second = _online_session_observations("root-123", events, 0, True, "completed", [])
    findings = _finding_map(first)

    assert set(findings) == {"command.nonzero_exit", "command.exact_repeat"}
    assert [item["id"] for item in first] == [item["id"] for item in second]
    assert all(item["status"] == "recorded" for item in first)
    assert findings["command.nonzero_exit"]["source_refs"] == [{
        "actor_thread_id": "root-123", "actor_index": 0, "event_index": 4,
        "timestamp": "2026-10-28T10:00:01Z",
    }]
    assert [ref["event_index"] for ref in findings["command.exact_repeat"]["source_refs"]] == [4, 7]
    assert "does not determine" in findings["command.nonzero_exit"]["summary"]
    assert "does not establish a retry loop" in findings["command.exact_repeat"]["summary"]


def test_missing_child_parse_errors_and_usage_are_reported_as_incomplete_evidence():
    children = [
        {"thread_id": "child-missing", "actor_index": 1, "rollout_captured": False,
         "start_ts": "2026-10-28T10:00:02Z", "waited": False},
        {"thread_id": "child-partial", "actor_index": 2, "rollout_captured": True,
         "start_ts": "2026-10-28T10:00:03Z", "end_ts": "2026-10-28T10:00:04Z",
         "events": [], "parse_errors": 2, "usage_observed": False, "waited": False},
    ]

    findings = _finding_map(_online_session_observations(
        "root-456", [], 1, False, None, children
    ))

    assert set(findings) == {
        "subagent.rollout_missing", "subagent.completion_unobserved",
        "trace.parse_errors", "usage.not_observed",
    }
    assert all(item["status"] == "provisional" for item in findings.values())
    assert all(item["completeness"] == "incomplete" for item in findings.values())
    assert findings["subagent.rollout_missing"]["source_refs"][0]["actor_thread_id"] == "child-missing"
    assert findings["subagent.completion_unobserved"]["source_refs"]
    assert "not a claim" in findings["subagent.completion_unobserved"]["summary"]
    assert findings["trace.parse_errors"]["summary"].startswith("The rollout parser skipped 3")
    assert "unknown, not zero" in findings["usage.not_observed"]["summary"]


def test_completed_session_without_signals_has_no_observation_card_content():
    assert _online_session_observations("root-clean", [], 0, True, "completed", []) == []


def test_new_turn_after_completed_turn_keeps_observations_provisional(tmp_path):
    rollout = tmp_path / "rollout-2026-10-28T10-00-00-root.jsonl"
    events = [
        {"type": "event_msg", "timestamp": "2026-10-28T10:00:01Z",
         "payload": {"type": "task_complete"}},
        {"type": "event_msg", "timestamp": "2026-10-28T10:01:00Z",
         "payload": {"type": "user_message", "message": "Another task"}},
        {"type": "event_msg", "timestamp": "2026-10-28T10:01:01Z",
         "payload": {"type": "task_started"}},
        {"type": "event_msg", "timestamp": "2026-10-28T10:01:02Z",
         "payload": {"type": "user_message", "message": "run command"}},
        {"type": "response_item", "timestamp": "2026-10-28T10:01:03Z",
         "payload": {"type": "function_call", "name": "exec_command",
                     "call_id": "cmd-1", "arguments": '{"cmd":"false"}'}},
        {"type": "response_item", "timestamp": "2026-10-28T10:01:04Z",
         "payload": {"type": "function_call_output", "call_id": "cmd-1",
                     "output": '{"exit_code":1}'}},
    ]
    rollout.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")

    parsed = parse_session_rollout(rollout)
    findings = _online_session_observations(
        parsed["thread_id"], parsed["events"], parsed["parse_errors"],
        parsed["usage_observed"], parsed["final_status"], [],
    )

    assert parsed["final_status"] == "in_progress"
    assert all(finding["status"] == "provisional" for finding in findings)


def test_opaque_spawn_arguments_are_not_retained_or_rendered():
    inspection = _rollout_inspection([
        {
            "type": "response_item",
            "timestamp": "2026-10-28T10:00:01Z",
            "payload": {
                "type": "function_call", "namespace": "collaboration",
                "name": "spawn_agent", "call_id": "spawn-1",
                "arguments": "gAAAA-encrypted-payload",
            },
        }
    ])

    spawn = next(event for event in inspection["events"] if event["kind"] == "spawn")
    assert spawn["prompt"] is None
    assert spawn["requested_profile"] is None
    assert spawn["prompt_status"] == "encrypted"
    assert spawn["profile_status"] == "encrypted"
    assert "gAAAA" not in repr(inspection)


def test_spawn_request_and_normalized_result_deduplicate_by_call_id():
    inspection = _rollout_inspection([
        {
            "type": "response_item", "timestamp": "2026-10-28T10:00:01Z",
            "payload": {
                "type": "function_call", "namespace": "collaboration",
                "name": "spawn_agent", "call_id": "spawn-2",
                "arguments": json.dumps({"agent_type": "reviewer", "message": "Review auth"}),
            },
        },
        {
            "type": "event_msg", "timestamp": "2026-10-28T10:00:02Z",
            "payload": {
                "type": "CollabAgentToolCall", "id": "spawn-2",
                "tool": "spawn_agent", "requested_profile": "reviewer",
                "prompt": "Review auth", "receiver_thread_ids": ["child-2"],
                "task_name": "auth-review",
            },
        },
    ])

    spawns = [event for event in inspection["events"] if event["kind"] == "spawn"]
    assert len(spawns) == 1
    assert spawns[0]["ts"] == "2026-10-28T10:00:01Z"
    assert spawns[0]["requested_profile"] == "reviewer"
    assert spawns[0]["thread_ids"] == ["child-2"]
    assert spawns[0]["spawn_task_name"] == "auth-review"


def test_captured_manifest_enriches_not_captured_profile_status(tmp_path):
    subagents_dir = tmp_path / "worker" / "subagents"
    subagents_dir.mkdir(parents=True)
    (subagents_dir / "manifest.json").write_text(json.dumps({
        "subagents": [{
            "thread_id": "child-3", "parent_thread_id": "root-3",
            "requested_profile": "security-reviewer", "profile_status": "captured",
            "prompt_status": "captured", "prompt": "Review auth boundaries",
        }]
    }), encoding="utf-8")
    by_tid = {"child-3": {
        "thread_id": "child-3", "rollout_captured": True,
        "profile_status": "not_captured", "prompt_status": "not_captured",
    }}

    _inject_captured_subagents(subagents_dir.parent, "root-3", by_tid, {})

    child = by_tid["child-3"]
    assert child["profile_status"] == "captured"
    assert child["prompt_status"] == "captured"
    assert child["requested_profile"] == "security-reviewer"
    assert child["spawn_prompt"] == "Review auth boundaries"


class EvidenceLinks(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids = set()
        self.locate_calls = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "button" and "observation-evidence" in attrs.get("class", "").split():
            self.locate_calls.append(attrs.get("onclick", ""))


class TimelineEvidence(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.actor = None
        self.actor_indexes = {}
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "section" and "u-trace-agent" in classes:
            self.actor = attrs.get("id")
            self.actor_indexes[self.actor] = set()
        elif tag == "div" and "u-event" in classes and self.actor:
            index = attrs.get("data-event-index")
            if index is not None:
                self.actor_indexes[self.actor].add(index)

    def handle_endtag(self, tag):
        if tag == "section" and self.actor:
            self.actor = None


def test_observation_locate_buttons_target_rendered_actor_events():
    session = {
        "thread_id": "root-789", "started_at": "2026-10-28T10:00:00Z",
        "model": "test-model", "skills_used": [], "turn_count": 1,
        "command_count": 1, "est_cost": 0, "token_usage": {
            "billed_output_tokens": 0, "uncached_input_tokens": 0,
            "cached_input_tokens": 0,
        },
        "observations": [{
            "id": "obs-command.nonzero_exit-test", "kind": "command.nonzero_exit",
            "level": "info", "status": "recorded", "completeness": "complete",
            "summary": "A command exited non-zero.", "analyzer_version": "1.0.0",
            "source_refs": [{"actor_thread_id": "root-789", "actor_index": 0,
                             "event_index": 0, "timestamp": "2026-10-28T10:00:01Z"},
                            {"actor_thread_id": "child-1", "actor_index": 1,
                             "event_index": 1, "timestamp": "2026-10-28T10:00:02Z"}],
        }],
        "activity_tree": {
            "thread_id": "root-789", "start_ts": "2026-10-28T10:00:00Z",
            "end_ts": "2026-10-28T10:00:04Z", "events": [
                {"kind": "cmd", "command": "false", "exit_code": 1,
                 "ts": "2026-10-28T10:00:01Z", "event_index": 0},
            ],
            "children": [{"thread_id": "child-1", "start_ts": "2026-10-28T10:00:02Z",
                          "end_ts": "2026-10-28T10:00:03Z", "events": [
                              {"kind": "cmd", "command": "true", "exit_code": 0,
                               "ts": "2026-10-28T10:00:02Z", "event_index": 1},
                          ]}],
        },
    }

    html = _real_session_details({"sessions": [session]})
    links = EvidenceLinks(html)
    timeline = TimelineEvidence(html)

    assert "real-sess-0-timeline-stage" in links.ids
    assert len(links.locate_calls) == 2
    for call in links.locate_calls:
        match = re.search(r"locateTimelineEvidence\('([^']+)','([^']+)',(-?\d+)\)", call)
        assert match, call
        stage_id, actor_id, event_index = match.groups()
        assert stage_id == "real-sess-0-timeline-stage"
        assert actor_id in timeline.actor_indexes
        assert event_index in timeline.actor_indexes[actor_id]


def test_session_observations_are_collapsed_behind_a_summary_disclosure():
    session = {
        "thread_id": "root-obs", "started_at": "2026-10-28T10:00:00Z",
        "model": "test-model", "skills_used": [], "turn_count": 1,
        "command_count": 1, "est_cost": 0, "token_usage": {
            "billed_output_tokens": 0, "uncached_input_tokens": 0,
            "cached_input_tokens": 0,
        },
        "observations": [{
            "id": "obs-1", "kind": "command.nonzero_exit", "level": "info",
            "status": "recorded", "completeness": "complete",
            "summary": "A command exited non-zero.", "analyzer_version": "1.0.0",
            "source_refs": [],
        }],
        "activity_tree": {
            "thread_id": "root-obs", "start_ts": "2026-10-28T10:00:00Z",
            "end_ts": "2026-10-28T10:00:04Z", "events": [], "children": [],
        },
    }

    html = _real_session_details({"sessions": [session]})
    # The panel body is wrapped in a closed <details>, with the headline count
    # on the one-line <summary>.
    assert "<details class='obs-details'>" in html
    assert "<summary class='obs-summary'>" in html
    assert "1 findings" in html
    # The finding content is still present inside, for expansion on click.
    assert "A command exited non-zero." in html


def test_turns_render_as_labeled_cost_bars_not_a_uuid_table():
    from _lib.usage_html import _turn_cards, _turn_label

    session = {
        "thread_id": "root-turns",
        "events": [
            {"kind": "msg", "role": "user", "ts": "2026-10-28T10:00:00Z", "event_index": 3,
             "text": "# Context from my IDE setup: ## Active file: a.py\nfix telemetry report"},
            {"kind": "msg", "role": "user", "ts": "2026-10-28T10:05:00Z", "event_index": 9,
             "text": "[$commit](/abs/path/to/commit) now please"},
        ],
        "turns": [
            {"root_turn_id": "01a1a986-first", "actors": ["root", "child"],
             "inclusive": {
                 "requests": [{"timestamp": "2026-10-28T10:00:05Z"}],
                 "tokens": {"billed_output_tokens": 14127},
                 "est_cost": 0.44, "known_cost": 0.44,
                 "coverage": {"status": "complete"}}},
            {"root_turn_id": "01a1a990-second", "actors": ["root"],
             "inclusive": {
                 "requests": [{"timestamp": "2026-10-28T10:05:10Z"}],
                 "tokens": {"billed_output_tokens": 2100},
                 "est_cost": 0.07, "known_cost": 0.07,
                 "coverage": {"status": "complete"}}},
        ],
    }

    # Labels are human, derived from the preceding user message, with IDE
    # boilerplate stripped and slash-command links surfaced.
    first_label, first_full, first_idx = _turn_label(session, session["turns"][0])
    assert first_label == "fix telemetry report"
    assert first_idx == 3
    assert "Context from my IDE setup" not in first_label
    second_label, _, second_idx = _turn_label(session, session["turns"][1])
    assert second_label.startswith("/commit")
    assert second_idx == 9

    html = _turn_cards(session, "real-sess-0")
    # Visual, not a raw table: cost meter bars + compact out-token labels.
    assert "turn-row" in html and "table-cost" in html and "meter-blue" in html
    assert "14.1k out" in html and "2.1k out" in html
    # The raw UUID is not the visible label.
    assert "01a1a986-first" not in html
    # Clicking a turn navigates to that turn's event on the timeline.
    assert "selectDetailTab('real-sess-0','timeline')" in html
    assert "locateTimelineEvidence('real-sess-0-timeline-stage'," in html


def test_turn_without_label_evidence_falls_back_to_short_id():
    from _lib.usage_html import _turn_label

    session = {"thread_id": "root", "events": []}
    turn = {"root_turn_id": "01a1a986-560b-70a3-abcd", "actors": [],
            "inclusive": {"requests": [{"timestamp": "2026-10-28T10:00:05Z"}],
                          "tokens": {"billed_output_tokens": 0},
                          "est_cost": None, "known_cost": None,
                          "coverage": {"status": "unavailable"}}}
    label, full, idx = _turn_label(session, turn)
    assert label == "01a1a986"
    # The unattributed sentinel stays readable rather than truncated.
    turn["root_turn_id"] = "unattributed"
    label, _, _ = _turn_label(session, turn)
    assert label == "unattributed"
