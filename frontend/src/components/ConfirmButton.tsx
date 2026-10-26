import type { ReactNode } from "react";

/** A button that asks `confirm()` first; used for every delete. */
export function ConfirmButton({
  message,
  onConfirm,
  disabled,
  className = "btn btn-danger",
  children,
}: {
  message: string;
  onConfirm: () => void;
  disabled?: boolean;
  className?: string;
  children: ReactNode;
}) {
  return (
    <button type="button" className={className} disabled={disabled} onClick={() => confirm(message) && onConfirm()}>
      {children}
    </button>
  );
}
