import { renderHook, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { usePolling } from "./usePolling"

const INTERVAL_MS = 30

describe("usePolling", () => {
  it("fetches immediately on mount and exposes the result", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ value: 1 })

    const { result } = renderHook(() => usePolling(fetchFn, INTERVAL_MS, []))

    await waitFor(() => expect(result.current.data).toEqual({ value: 1 }))
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it("polls again after the interval elapses", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ value: 1 })

    renderHook(() => usePolling(fetchFn, INTERVAL_MS, []))
    await waitFor(() => expect(fetchFn).toHaveBeenCalledTimes(1))

    await waitFor(() => expect(fetchFn.mock.calls.length).toBeGreaterThanOrEqual(2))
  })

  it("keeps the last-known-good data and sets an error on failure", async () => {
    const fetchFn = vi
      .fn()
      .mockResolvedValueOnce({ value: 1 })
      .mockRejectedValue(new Error("network down"))

    const { result } = renderHook(() => usePolling(fetchFn, INTERVAL_MS, []))
    await waitFor(() => expect(result.current.data).toEqual({ value: 1 }))

    await waitFor(() => expect(result.current.error).toBe("network down"))
    expect(result.current.data).toEqual({ value: 1 })
  })

  it("resets and refetches when deps change", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ value: 1 })

    const { rerender } = renderHook(
      ({ dep }) => usePolling(fetchFn, INTERVAL_MS, [dep]),
      { initialProps: { dep: "a" } },
    )
    await waitFor(() => expect(fetchFn).toHaveBeenCalledTimes(1))

    rerender({ dep: "b" })
    await waitFor(() => expect(fetchFn.mock.calls.length).toBeGreaterThanOrEqual(2))
  })
})
