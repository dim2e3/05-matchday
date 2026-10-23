import { render, screen } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import * as api from "../api"
import { Notifications } from "./Notifications"

vi.mock("../api")
const mockedApi = vi.mocked(api)

describe("Notifications", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("S6: lists notifications with delivery status", async () => {
    mockedApi.fetchNotifications.mockResolvedValue([
      {
        kind: "final",
        league: "nhl",
        text: "🏁 Final: DAL 2 – 3 STL (NHL)",
        status: "sent",
        created_at: "2026-10-23T02:00:00Z",
        sent_at: "2026-10-23T02:00:05Z",
      },
      {
        kind: "kickoff",
        league: "nhl",
        text: "🟢 Kickoff: DAL @ STL (NHL)",
        status: "failed",
        created_at: "2026-10-23T00:00:00Z",
        sent_at: null,
      },
    ])

    render(<Notifications />)

    expect(await screen.findByText("🏁 Final: DAL 2 – 3 STL (NHL)")).toBeInTheDocument()
    expect(screen.getByText("Delivered")).toBeInTheDocument()
    expect(screen.getByText("Failed")).toBeInTheDocument()
  })

  it("S6: empty state explains how to get notifications", async () => {
    mockedApi.fetchNotifications.mockResolvedValue([])

    render(<Notifications />)

    expect(await screen.findByText(/No notifications yet/)).toBeInTheDocument()
  })
})
