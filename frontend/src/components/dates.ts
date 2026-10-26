// Backend sends UTC ISO strings; show them in the browser's local time (frontend-spec §6).

const dateTime = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });
const relative = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });

export const formatDate = (iso: string) => dateTime.format(new Date(iso));

export function formatRelative(iso: string, now = Date.now()) {
  const seconds = Math.round((new Date(iso).getTime() - now) / 1000);
  const abs = Math.abs(seconds);
  if (abs < 60) return relative.format(seconds, "second");
  if (abs < 3600) return relative.format(Math.round(seconds / 60), "minute");
  if (abs < 86_400) return relative.format(Math.round(seconds / 3600), "hour");
  return relative.format(Math.round(seconds / 86_400), "day");
}

export function formatElapsed(fromIso: string, now = Date.now()) {
  const s = Math.max(0, Math.floor((now - new Date(fromIso).getTime()) / 1000));
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`;
}

const pad = (n: number) => String(n).padStart(2, "0");

/** UTC ISO → `datetime-local` input value in the browser's time zone. */
export function toLocalInput(iso: string) {
  const d = new Date(iso);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** `datetime-local` value (local time) → UTC ISO; empty → null. */
export const fromLocalInput = (value: string) => (value ? new Date(value).toISOString() : null);
