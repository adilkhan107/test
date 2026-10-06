import type { Risk, Status } from "../services/api";

export const mmss = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
export const when = (iso: string) =>
  new Date(iso).toLocaleString(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

export const TYPE_LABEL: Record<string, string> = {
  no_hardhat: "No hardhat",
  no_vest: "No safety vest",
  no_mask: "No mask",
};

/** Hazard-tape progress bar: the striped part is the value. */
export function HazardBar({ value, label }: { value: number; label: string }) {
  const v = Math.max(0, Math.min(100, value));
  return (
    <div className="hazard" role="progressbar" aria-label={label} aria-valuenow={Math.round(v)} aria-valuemin={0} aria-valuemax={100}>
      <div className="hazard-fill" style={{ width: `${v}%` }} />
    </div>
  );
}

export function RiskBadge({ level }: { level: Risk | null }) {
  if (!level) return <span className="muted">-</span>;
  return <span className={`badge risk-${level}`}>{level === "unknown" ? "No workers found" : `${level} risk`}</span>;
}

const STATUS_TEXT: Record<Status, string> = {
  queued: "Waiting",
  processing: "Analyzing",
  completed: "Done",
  failed: "Failed",
};
export function StatusPill({ status }: { status: Status }) {
  return <span className={`pill status-${status}`}>{STATUS_TEXT[status]}</span>;
}

export function ErrorNote({ message }: { message: string }) {
  return <p className="error" role="alert">{message}</p>;
}

export function Loading({ text = "Loading" }: { text?: string }) {
  return <p className="muted">{text}...</p>;
}
