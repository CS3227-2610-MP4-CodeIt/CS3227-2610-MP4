import { useRef, useState, type CSSProperties, type KeyboardEvent, type PointerEvent, type ReactNode } from "react";

const MIN = 25;
const MAX = 75;
const STEP = 2;

const clamp = (percent: number) => Math.min(MAX, Math.max(MIN, percent));

/**
 * Two columns with a draggable divider (mouse, touch or arrow keys) on wide screens; stacked below
 * `lg`, where the divider is hidden. The left column's width is a percentage of the whole.
 */
export function SplitPane({
  left,
  right,
  label,
  initial = 50,
}: {
  left: ReactNode;
  right: ReactNode;
  label: string;
  initial?: number;
}) {
  const container = useRef<HTMLDivElement>(null);
  const [split, setSplit] = useState(initial);

  const onPointerMove = (e: PointerEvent<HTMLDivElement>) => {
    if (!e.currentTarget.hasPointerCapture(e.pointerId) || !container.current) return;
    const box = container.current.getBoundingClientRect();
    setSplit(clamp(((e.clientX - box.left) / box.width) * 100));
  };

  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "ArrowLeft") setSplit((s) => clamp(s - STEP));
    else if (e.key === "ArrowRight") setSplit((s) => clamp(s + STEP));
    else return;
    e.preventDefault();
  };

  return (
    <div
      ref={container}
      style={{ "--split": `${split}%` } as CSSProperties}
      className="grid gap-6 lg:grid-cols-[minmax(0,var(--split))_0.75rem_minmax(0,1fr)] lg:gap-1.5"
    >
      {left}
      <div
        role="separator"
        aria-orientation="vertical"
        aria-label={label}
        aria-valuenow={Math.round(split)}
        aria-valuemin={MIN}
        aria-valuemax={MAX}
        tabIndex={0}
        className="hidden cursor-col-resize touch-none justify-center rounded select-none hover:bg-slate-200 focus:bg-slate-200 focus:outline-none lg:flex"
        onPointerDown={(e) => {
          e.preventDefault();
          e.currentTarget.setPointerCapture(e.pointerId);
        }}
        onPointerMove={onPointerMove}
        onKeyDown={onKeyDown}
      >
        <span className="w-0.5 rounded bg-slate-300" />
      </div>
      {right}
    </div>
  );
}
