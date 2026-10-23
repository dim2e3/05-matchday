import { useEffect, useRef, useState } from "react"

interface PollingState<T> {
  data: T | null
  error: string | null
  isLoading: boolean
  isRefreshing: boolean
}

export function usePolling<T>(
  fetchFn: () => Promise<T>,
  intervalMs: number,
  deps: unknown[],
): PollingState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const fetchFnRef = useRef(fetchFn)
  fetchFnRef.current = fetchFn

  useEffect(() => {
    let cancelled = false
    let hasLoadedOnce = false

    setIsLoading(true)
    setData(null)
    setError(null)

    async function poll() {
      if (document.visibilityState === "hidden") {
        return
      }
      if (hasLoadedOnce) {
        setIsRefreshing(true)
      }
      try {
        const result = await fetchFnRef.current()
        if (cancelled) return
        setData(result)
        setError(null)
      } catch (err) {
        if (cancelled) return
        setError(err instanceof Error ? err.message : "Unknown error")
      } finally {
        if (!cancelled) {
          hasLoadedOnce = true
          setIsLoading(false)
          setIsRefreshing(false)
        }
      }
    }

    poll()
    const id = setInterval(poll, intervalMs)

    return () => {
      cancelled = true
      clearInterval(id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, error, isLoading, isRefreshing }
}
