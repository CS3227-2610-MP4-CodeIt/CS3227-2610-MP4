import { useRef, type ReactNode } from "react";

export type Tab = "run" | "submit" | "hint" | "submissions";
const tabs: { id: Tab; label: string }[] = [
  { id: "run", label: "Run result" },
  { id: "submit", label: "Submit result" },
  { id: "hint", label: "Hint" },
  { id: "submissions", label: "Submissions" },
];

export function nextResultTab(current: Tab, key: string): Tab | null {
  const index = tabs.findIndex((tab) => tab.id === current);
  if (key === "Home") return tabs[0].id;
  if (key === "End") return tabs[tabs.length - 1].id;
  if (key === "ArrowRight") return tabs[(index + 1) % tabs.length].id;
  if (key === "ArrowLeft")
    return tabs[(index + tabs.length - 1) % tabs.length].id;
  return null;
}

export function ResultTabs({
  selected,
  onSelect,
  panels,
}: {
  selected: Tab;
  onSelect: (tab: Tab) => void;
  panels: Record<Tab, ReactNode>;
}) {
  const refs = useRef<Partial<Record<Tab, HTMLButtonElement>>>({});
  return (
    <>
      <div
        className="flex flex-wrap gap-1 border-b border-slate-200 pb-2"
        role="tablist"
        aria-label="Question results"
      >
        {tabs.map(({ id, label }) => (
          <button
            key={id}
            ref={(node) => {
              if (node) refs.current[id] = node;
            }}
            id={`result-tab-${id}`}
            role="tab"
            type="button"
            aria-selected={selected === id}
            aria-controls={`result-panel-${id}`}
            tabIndex={selected === id ? 0 : -1}
            onClick={() => onSelect(id)}
            onKeyDown={(event) => {
              const next = nextResultTab(id, event.key);
              if (next) {
                event.preventDefault();
                onSelect(next);
                refs.current[next]?.focus();
              }
            }}
            className={`rounded px-2 py-2 text-sm ${selected === id ? "bg-slate-200 font-medium" : "text-slate-600 hover:bg-slate-100"}`}
          >
            {label}
          </button>
        ))}
      </div>
      {tabs.map(({ id }) => (
        <div
          key={id}
          id={`result-panel-${id}`}
          role="tabpanel"
          aria-labelledby={`result-tab-${id}`}
          hidden={selected !== id}
          tabIndex={selected === id ? 0 : undefined}
        >
          {selected === id && panels[id]}
        </div>
      ))}
    </>
  );
}
