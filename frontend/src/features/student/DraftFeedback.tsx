import { useDraftSaver } from "./useDraftSaver";

export function DraftStatus({
  status,
}: {
  status: ReturnType<typeof useDraftSaver>["status"];
}) {
  if (!status) return null;
  const labels = {
    saving: "Saving draft…",
    saved: "Draft saved on this device",
    unavailable: "Draft could not be saved on this device",
  };
  return (
    <p
      role="status"
      className={`text-xs ${status === "unavailable" ? "text-red-700" : "text-slate-500"}`}
    >
      {labels[status]}
    </p>
  );
}

export function DraftGuidance({ origin }: { origin: string | null }) {
  return (
    <p className="text-xs text-slate-600">
      {origin ?? "Loading your starting code…"} Drafts are kept on this device
      when available; submit to send your code.
    </p>
  );
}
