import { ApiError } from "../api/client";

/** The field a 422 validation item points at (`loc` last element), or null. */
const itemField = (loc: (string | number)[]) => {
  const last = loc[loc.length - 1];
  return typeof last === "string" && last !== "body" ? last : null;
};

/** Message for one form field from a 422 validation list (frontend-spec §3.4). */
function fieldError(error: unknown, field: string): string | null {
  if (!(error instanceof ApiError) || typeof error.detail === "string") return null;
  const item = error.detail.find((i) => itemField(i.loc) === field);
  return item ? item.msg : null;
}

export function FieldError({ error, field }: { error: unknown; field: string }) {
  const msg = fieldError(error, field);
  return msg ? <p className="mt-1 text-xs text-red-600">{msg}</p> : null;
}

/** Lines to show for an error; `fields` are left out because the form shows them by its inputs. */
function errorLines(error: unknown, fields: string[], messages: Record<number, string>): string[] | null {
  if (!(error instanceof ApiError) || error.status >= 500) return null;
  if (messages[error.status]) return [messages[error.status]];
  if (error.status === 403) return ["Not allowed."];
  if (typeof error.detail === "string") return [error.detail];
  return error.detail
    .filter((i) => !fields.includes(itemField(i.loc) ?? ""))
    .map((i) => (itemField(i.loc) ? `${itemField(i.loc)}: ${i.msg}` : i.msg));
}

export function ErrorText({
  error,
  onRetry,
  fields = [],
  messages = {},
}: {
  error: unknown;
  onRetry?: () => void;
  fields?: string[];
  /** Friendlier text per status, e.g. `{409: "Username already taken"}`. */
  messages?: Record<number, string>;
}) {
  if (!error) return null;
  const lines = errorLines(error, fields, messages);
  if (lines === null) {
    return (
      <div className="flex items-center gap-2 text-sm text-red-600">
        Could not reach the server. Try again.
        {onRetry && (
          <button type="button" className="btn" onClick={onRetry}>
            Retry
          </button>
        )}
      </div>
    );
  }
  if (lines.length === 0) return null;
  return (
    <div className="text-sm text-red-600">
      {lines.map((line, i) => (
        <p key={i}>{line}</p>
      ))}
    </div>
  );
}
