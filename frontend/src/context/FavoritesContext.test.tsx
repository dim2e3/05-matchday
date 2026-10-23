import { act, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"
import * as api from "../api"
import { FavoritesProvider, useFavorites } from "./FavoritesContext"

vi.mock("../api")
const mockedApi = vi.mocked(api)

function Probe() {
  const { isFavorite, toggleFavorite, isReady } = useFavorites()
  return (
    <div>
      <span data-testid="ready">{String(isReady)}</span>
      <span data-testid="fav">{String(isFavorite("nfl", "26"))}</span>
      <button
        onClick={() => toggleFavorite("nfl", "26", "Seattle Seahawks", "SEA")}
      >
        toggle
      </button>
    </div>
  )
}

describe("FavoritesContext", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("loads favorites on mount", async () => {
    mockedApi.fetchFavorites.mockResolvedValue([
      {
        league: "nfl",
        team_id: "26",
        team_name: "Seattle Seahawks",
        abbreviation: "SEA",
        added_at: "2026-09-12T00:00:00Z",
      },
    ])

    render(
      <FavoritesProvider>
        <Probe />
      </FavoritesProvider>,
    )

    await waitFor(() => expect(screen.getByTestId("ready")).toHaveTextContent("true"))
    expect(screen.getByTestId("fav")).toHaveTextContent("true")
  })

  it("treats fetch failure as an empty favorites list", async () => {
    mockedApi.fetchFavorites.mockRejectedValue(new Error("boom"))

    render(
      <FavoritesProvider>
        <Probe />
      </FavoritesProvider>,
    )

    await waitFor(() => expect(screen.getByTestId("ready")).toHaveTextContent("true"))
    expect(screen.getByTestId("fav")).toHaveTextContent("false")
  })

  it("optimistically toggles favorite state and calls addFavorite", async () => {
    mockedApi.fetchFavorites.mockResolvedValue([])
    mockedApi.addFavorite.mockResolvedValue({
      league: "nfl",
      team_id: "26",
      team_name: "Seattle Seahawks",
      abbreviation: "SEA",
      added_at: "2026-09-12T00:00:00Z",
    })
    const user = userEvent.setup()

    render(
      <FavoritesProvider>
        <Probe />
      </FavoritesProvider>,
    )
    await waitFor(() => expect(screen.getByTestId("ready")).toHaveTextContent("true"))

    await user.click(screen.getByText("toggle"))

    expect(screen.getByTestId("fav")).toHaveTextContent("true")
    expect(mockedApi.addFavorite).toHaveBeenCalledWith(
      "nfl",
      "26",
      "Seattle Seahawks",
      "SEA",
    )
  })

  it("rolls back the optimistic update if addFavorite fails", async () => {
    mockedApi.fetchFavorites.mockResolvedValue([])
    mockedApi.addFavorite.mockRejectedValue(new Error("boom"))
    const user = userEvent.setup()

    render(
      <FavoritesProvider>
        <Probe />
      </FavoritesProvider>,
    )
    await waitFor(() => expect(screen.getByTestId("ready")).toHaveTextContent("true"))

    await act(async () => {
      await user.click(screen.getByText("toggle"))
    })

    await waitFor(() => expect(screen.getByTestId("fav")).toHaveTextContent("false"))
  })
})
