import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"
import * as api from "../api"
import { FavoritesProvider } from "../context/FavoritesContext"
import { makeGame } from "../test/fixtures"
import { GameCard } from "./GameCard"

vi.mock("../api")
const mockedApi = vi.mocked(api)

function renderWithFavorites(ui: React.ReactElement) {
  return render(<FavoritesProvider>{ui}</FavoritesProvider>)
}

describe("GameCard", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedApi.fetchFavorites.mockResolvedValue([])
  })

  it("renders both teams, scores, and the live badge", () => {
    renderWithFavorites(<GameCard game={makeGame()} />)

    expect(screen.getByText("New England Patriots")).toBeInTheDocument()
    expect(screen.getByText("Seattle Seahawks")).toBeInTheDocument()
    expect(screen.getByText("10")).toBeInTheDocument()
    expect(screen.getByText("13")).toBeInTheDocument()
    expect(screen.getByText("LIVE")).toBeInTheDocument()
  })

  it("shows a league badge when requested", () => {
    renderWithFavorites(<GameCard game={makeGame()} showLeagueBadge />)
    expect(screen.getByText("NFL")).toBeInTheDocument()
  })

  it("omits the league badge by default", () => {
    renderWithFavorites(<GameCard game={makeGame()} />)
    expect(screen.queryByText("NFL")).not.toBeInTheDocument()
  })

  it("toggles a team's favorite star on click", async () => {
    mockedApi.addFavorite.mockResolvedValue({
      league: "nfl",
      team_id: "26",
      team_name: "Seattle Seahawks",
      abbreviation: "SEA",
      added_at: "2026-09-12T00:00:00Z",
    })
    const user = userEvent.setup()

    renderWithFavorites(<GameCard game={makeGame()} />)

    const star = await screen.findByLabelText("Favorite Seattle Seahawks")
    await user.click(star)

    expect(await screen.findByLabelText("Unfavorite Seattle Seahawks")).toBeInTheDocument()
    expect(mockedApi.addFavorite).toHaveBeenCalledWith(
      "nfl",
      "26",
      "Seattle Seahawks",
      "SEA",
    )
  })
})
