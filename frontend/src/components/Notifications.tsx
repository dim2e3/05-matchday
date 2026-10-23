import { fetchNotifications } from "../api"
import { usePolling } from "../hooks/usePolling"
import type { NotificationItem } from "../types"
import { ErrorBanner } from "./ErrorBanner"

const STATUS_LABELS: Record<NotificationItem["status"], string> = {
  pending: "Sending…",
  sent: "Delivered",
  failed: "Failed",
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    weekday: "short",
    hour: "numeric",
    minute: "2-digit",
  })
}

export function Notifications() {
  const { data, error, isLoading } = usePolling(fetchNotifications, 30_000, [])

  if (isLoading) {
    return <div className="status-text">Loading notifications…</div>
  }
  if (error && !data) {
    return <ErrorBanner message="Couldn't load notifications." />
  }
  if (!data || data.length === 0) {
    return (
      <div className="status-text">
        No notifications yet. Connect Telegram and you'll get one at kickoff and at the
        final score.
      </div>
    )
  }

  return (
    <ul className="notification-list">
      {data.map((n, i) => (
        <li key={`${n.created_at}-${i}`} className="notification">
          <span className="notification-text">{n.text}</span>
          <span className={`notification-status status-${n.status}`}>
            {STATUS_LABELS[n.status]}
          </span>
          <span className="notification-time">{formatTime(n.sent_at ?? n.created_at)}</span>
        </li>
      ))}
    </ul>
  )
}
