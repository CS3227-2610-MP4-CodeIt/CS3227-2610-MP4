import { useState } from "react";
import type { JudgeResult, JudgeTestResult, VisibleTestCase } from "../../api/types";
import { formatDate } from "../../components/dates";
import { formatMemory, VERDICT_CLASS, VERDICT_LABEL } from "./verdict";

/**
 * Result of a run or submit job (frontend-student §3.1). `visibleTests` are the statement's tests;
 * result `index` i of a visible test is visible test i (the backend sends visible tests first).
 */
export function JudgeResultView({
  result,
  sentAt,
  visibleTests,
}: {
  result: JudgeResult;
  sentAt: string;
  visibleTests: VisibleTestCase[];
}) {
  return (
    <div className="space-y-3">
      <div>
        <p className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
          <span className={`text-lg font-semibold ${VERDICT_CLASS[result.verdict]}`}>{VERDICT_LABEL[result.verdict]}</span>
          <span className="text-sm">{result.passed} / {result.total} passed</span>
          <span className="text-sm text-slate-600">
            max {result.max_time_ms} ms · {formatMemory(result.max_memory_kb)}
          </span>
        </p>
        <p className="text-xs text-slate-500">Result for the code sent at {formatDate(sentAt)}</p>
      </div>
      {result.error_message && (
        <pre className="max-h-48 overflow-auto rounded bg-red-50 p-2 font-mono text-xs whitespace-pre-wrap text-red-800">
          {result.error_message}
        </pre>
      )}
      <ul className="divide-y divide-slate-100 rounded border border-slate-200">
        {result.results.map((r) => (
          <TestRow key={r.index} result={r} expected={r.hidden ? undefined : visibleTests[r.index]} />
        ))}
      </ul>
      {result.results.length < result.total && (
        <p className="text-xs text-slate-500">Judging stops at the first failing test; the rest were not run.</p>
      )}
    </div>
  );
}

function TestRow({ result: r, expected }: { result: JudgeTestResult; expected?: VisibleTestCase }) {
  const [open, setOpen] = useState(false);
  const summary = (
    <>
      <span className="w-16 shrink-0 font-medium">Test {r.index + 1}</span>
      <span className={`w-44 shrink-0 ${VERDICT_CLASS[r.status]}`}>{VERDICT_LABEL[r.status]}</span>
      <span className="text-slate-600">{r.time_ms} ms · {formatMemory(r.memory_kb)}</span>
    </>
  );
  if (r.hidden) {
    return (
      <li className="flex flex-wrap items-center gap-x-3 px-3 py-1.5 text-sm">
        {summary}
        <span className="ml-auto text-xs text-slate-400">Hidden test</span>
      </li>
    );
  }
  return (
    <li className="text-sm">
      <button
        type="button"
        className="flex w-full flex-wrap items-center gap-x-3 px-3 py-1.5 text-left hover:bg-slate-50"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        {summary}
        <span className="ml-auto text-xs text-slate-400">{open ? "▾" : "▸"} details</span>
      </button>
      {open && (
        <div className="grid gap-2 px-3 pb-3 md:grid-cols-2">
          {/* The judge only returns output for the failed test (executor spec §3.1). */}
          <Output
            label="Your output"
            text={r.stdout_preview}
            missing={r.status === "ACCEPTED" ? "Matches the expected output." : "No output captured."}
          />
          <Output label="Expected output" text={expected?.expected_stdout} missing="(not available)" />
          {r.stderr_preview && <Output label="stderr" text={r.stderr_preview} missing="" wide />}
        </div>
      )}
    </li>
  );
}

function Output({ label, text, missing, wide }: { label: string; text?: string; missing: string; wide?: boolean }) {
  return (
    <div className={wide ? "md:col-span-2" : undefined}>
      <p className="mb-1 text-xs font-medium text-slate-500">{label}</p>
      <pre className="max-h-48 overflow-auto rounded bg-slate-100 p-2 font-mono text-xs whitespace-pre-wrap">
        {text ?? <span className="font-sans text-slate-500">{missing}</span>}
      </pre>
    </div>
  );
}
