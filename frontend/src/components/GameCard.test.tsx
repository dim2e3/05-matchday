import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"
import * as api from "../api"
import { FollowsProvider } from "../context/FollowsContext"
import { makeGame } from "../test/fixtures"
import { GameCard } from "./GameCard"

vi.mock("../api")
const mockedApi = vi.mocked(api)

function renderWithFollows(ui: React.ReactElement) {
  return render(<FollowsProvider>{ui}</FollowsProvider>)
}

describe("GameCard", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedApi.fetchFollows.mockResolvedValue([])
  })

  it("renders both teams, scores, and the live badge", () => {
    renderWithFollows(<GameCard game={makeGame()} />)

    expect(screen.getByText("New England Patriots")).toBeInTheDocument()
    expect(screen.getByText("Seattle Seahawks")).toBeInTheDocument()
    expect(screen.getByText("10")).toBeInTheDocument()
    expect(screen.getByText("13")).toBeInTheDocument()
    expect(screen.getByText("LIVE")).toBeInTheDocument()
  })

  it("shows a league badge when requested", () => {
    renderWithFollows(<GameCard game={makeGame()} showLeagueBadge />)
    expect(screen.getByText("NFL")).toBeInTheDocument()
  })

  it("shows FINAL for finished games", () => {
    renderWithFollows(
      <GameCard game={makeGame({ status_state: "post", status_detail: "Final" })} />,
    )
    expect(screen.getByText("FINAL")).toBeInTheDocument()
  })

  it("follows a team from its star", async () => {
    mockedApi.followTeam.mockResolvedValue({
      league: "nfl",
      team_id: "26",
      team_name: "Seattle Seahawks",
      abbreviation: "SEA",
      logo: null,
      created_at: "2026-10-23T00:00:00Z",
    })
    const user = userEvent.setup()
    renderWithFollows(<GameCard game={makeGame()} />)

    await user.click(await screen.findByLabelText("Follow Seattle Seahawks"))

    expect(await screen.findByLabelText("Unfollow Seattle Seahawks")).toBeInTheDocument()
    expect(mockedApi.followTeam).toHaveBeenCalledWith("nfl", "26")
  })
})
