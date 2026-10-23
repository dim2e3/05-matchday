import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"
import * as api from "../api"
import { FollowsProvider } from "../context/FollowsContext"
import { makeGame } from "../test/fixtures"
import type { Follow } from "../types"
import { MyGames } from "./MyGames"

vi.mock("../api")
const mockedApi = vi.mocked(api)

const FOLLOW: Follow = {
  league: "nfl",
  team_id: "26",
  team_name: "Seattle Seahawks",
  abbreviation: "SEA",
  logo: null,
  created_at: "2026-10-23T00:00:00Z",
}

function renderMyGames(onFindTeams = vi.fn()) {
  return render(
    <FollowsProvider>
      <MyGames onFindTeams={onFindTeams} />
    </FollowsProvider>,
  )
}

describe("MyGames", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedApi.fetchFollows.mockResolvedValue([FOLLOW])
  })

  it("S3: shows followed games with league badge and live score", async () => {
    mockedApi.fetchMyGames.mockResolvedValue({
      fetched_at: "2026-10-23T00:00:00Z",
      stale: false,
      games: [makeGame()],
    })

    renderMyGames()

    expect(await screen.findByText("Seattle Seahawks")).toBeInTheDocument()
    expect(screen.getByText("NFL")).toBeInTheDocument()
    expect(screen.getByText("LIVE")).toBeInTheDocument()
  })

  it("S3: with no follows prompts to find teams", async () => {
    mockedApi.fetchFollows.mockResolvedValue([])
    mockedApi.fetchMyGames.mockResolvedValue({
      fetched_at: "2026-10-23T00:00:00Z",
      stale: false,
      games: [],
    })
    const onFindTeams = vi.fn()
    const user = userEvent.setup()

    renderMyGames(onFindTeams)
    await user.click(await screen.findByText("Find teams"))

    expect(screen.getByText("Follow a team to see their games here.")).toBeInTheDocument()
    expect(onFindTeams).toHaveBeenCalled()
  })

  it("S3: follows but no games today", async () => {
    mockedApi.fetchMyGames.mockResolvedValue({
      fetched_at: "2026-10-23T00:00:00Z",
      stale: false,
      games: [],
    })

    renderMyGames()

    expect(
      await screen.findByText("No games today for the teams you follow."),
    ).toBeInTheDocument()
  })

  it("S3: stale data shows the out-of-date banner", async () => {
    mockedApi.fetchMyGames.mockResolvedValue({
      fetched_at: "2026-10-23T00:00:00Z",
      stale: true,
      games: [makeGame()],
    })

    renderMyGames()

    expect(await screen.findByText(/Scores may be out of date/)).toBeInTheDocument()
    expect(screen.getByText("Seattle Seahawks")).toBeInTheDocument()
  })

  it("S3: hard failure shows an error", async () => {
    mockedApi.fetchMyGames.mockRejectedValue(new api.ApiError(502))

    renderMyGames()

    expect(await screen.findByText("Couldn't load live scores. Retrying…")).toBeInTheDocument()
  })
})
