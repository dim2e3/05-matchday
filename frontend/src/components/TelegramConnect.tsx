import { useCallback, useEffect, useState } from "react"
import { createTelegramLink, disconnectTelegram, fetchMe } from "../api"

export function TelegramConnect() {
  const [connected, setConnected] = useState<boolean | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(false)

  const refresh = useCallback(() => {
    fetchMe()
      .then((me) => setConnected(me.telegram_connected))
      .catch(() => setConnected(false))
  }, [])

  useEffect(() => {
    refresh()
    // Coming back from the Telegram app: re-check whether the link completed.
    const onVisible = () => document.visibilityState === "visible" && refresh()
    document.addEventListener("visibilitychange", onVisible)
    return () => document.removeEventListener("visibilitychange", onVisible)
  }, [refresh])

  async function connect() {
    setBusy(true)
    setError(false)
    try {
      const { url } = await createTelegramLink()
      window.open(url, "_blank", "noopener")
    } catch {
      setError(true)
    } finally {
      setBusy(false)
    }
  }

  async function disconnect() {
    setBusy(true)
    try {
      await disconnectTelegram()
      setConnected(false)
    } catch {
      setError(true)
    } finally {
      setBusy(false)
    }
  }

  if (connected === null) {
    return null
  }

  return (
    <div className="telegram-connect">
      {connected ? (
        <>
          <span className="telegram-status">✅ Telegram connected</span>
          <button className="link-button" onClick={disconnect} disabled={busy}>
            Disconnect
          </button>
        </>
      ) : (
        <button className="primary" onClick={connect} disabled={busy}>
          Connect Telegram
        </button>
      )}
      {error && <span className="telegram-error">Something went wrong, try again.</span>}
    </div>
  )
}
