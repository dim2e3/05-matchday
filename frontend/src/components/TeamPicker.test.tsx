import { render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"
import * as api from "../api"
import { FollowsProvider } from "../context/FollowsContext"
import { TeamPicker } from "./TeamPicker"

vi.mock("../api")
const mockedApi = vi.mocked(api)

const NHL_TEAMS = [
  { id: "9", name: "Dallas Stars", abbreviation: "DAL", logo: null },
  { id: "19", name: "St. Louis Blues", abbreviation: "STL", logo: null },
  { id: "21", name: "Toronto Maple Leafs", abbreviation: "TOR", logo: null },
]

function renderPicker() {
  return render(
    <FollowsProvider>
      <TeamPicker />
    </FollowsProvider>,
  )
}

describe("TeamPicker", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedApi.fetchTeams.mockImplementation(async (league) =>
      league === "nhl" ? NHL_TEAMS : [],
    )
    mockedApi.fetchFollows.mockResolvedValue([
      {
        league: "nhl",
        team_id: "21",
        team_name: "Toronto Maple Leafs",
        abbreviation: "TOR",
        logo: null,
        created_at: "2026-10-23T00:00:00Z",
      },
    ])
  })

  it("S2: switching league loads its teams, followed teams first", async () => {
    const user = userEvent.setup()
    renderPicker()

    await user.click(screen.getByRole("tab", { name: "NHL" }))

    await screen.findByText("Dallas Stars")
    const names = within(screen.getByRole("list"))
      .getAllByRole("listitem")
      .map((li) => li.textContent)
    expect(names[0]).toContain("Toronto Maple Leafs")
    expect(mockedApi.fetchTeams).toHaveBeenCalledWith("nhl")
  })

  it("S2: search filters by name or abbreviation", async () => {
    const user = userEvent.setup()
    renderPicker()
    await user.click(screen.getByRole("tab", { name: "NHL" }))
    await screen.findByText("Dallas Stars")

    await user.type(screen.getByLabelText("Search teams"), "stl")

    expect(screen.getByText("St. Louis Blues")).toBeInTheDocument()
    expect(screen.queryByText("Dallas Stars")).not.toBeInTheDocument()
  })

  it("S2: follow toggle calls the API", async () => {
    mockedApi.followTeam.mockResolvedValue({
      league: "nhl",
      team_id: "19",
      team_name: "St. Louis Blues",
      abbreviation: "STL",
      logo: null,
      created_at: "2026-10-23T00:00:00Z",
    })
    const user = userEvent.setup()
    renderPicker()
    await user.click(screen.getByRole("tab", { name: "NHL" }))

    await user.click(await screen.findByLabelText("Follow St. Louis Blues"))

    expect(mockedApi.followTeam).toHaveBeenCalledWith("nhl", "19")
  })

  it("S2: shows an error when teams fail to load", async () => {
    mockedApi.fetchTeams.mockRejectedValue(new api.ApiError(502))

    renderPicker()

    expect(await screen.findByText(/Couldn't load teams/)).toBeInTheDocument()
  })
})
