import type { StatusState } from "../types"

interface StatusBadgeProps {
  state: StatusState
  detail: string
}

export function StatusBadge({ state, detail }: StatusBadgeProps) {
  const className =
    state === "in"
      ? "status-badge status-live"
      : state === "post"
        ? "status-badge status-final"
        : "status-badge status-scheduled"

  const label = state === "in" ? "LIVE" : state === "post" ? "FINAL" : detail

  return <span className={className}>{label}</span>
}
