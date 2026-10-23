import { act, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"
import * as api from "../api"
import { FollowsProvider, useFollows } from "./FollowsContext"

vi.mock("../api")
const mockedApi = vi.mocked(api)

const STL_FOLLOW = {
  league: "nhl" as const,
  team_id: "19",
  team_name: "St. Louis Blues",
  abbreviation: "STL",
  logo: null,
  created_at: "2026-10-23T00:00:00Z",
}

function Probe() {
  const { isFollowed, toggleFollow, isReady, count } = useFollows()
  return (
    <div>
      <span data-testid="ready">{String(isReady)}</span>
      <span data-testid="followed">{String(isFollowed("nhl", "19"))}</span>
      <span data-testid="count">{count}</span>
      <button onClick={() => toggleFollow("nhl", "19")}>toggle</button>
    </div>
  )
}

function renderProbe() {
  return render(
    <FollowsProvider>
      <Probe />
    </FollowsProvider>,
  )
}

describe("FollowsContext", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("loads follows on mount", async () => {
    mockedApi.fetchFollows.mockResolvedValue([STL_FOLLOW])

    renderProbe()

    await waitFor(() => expect(screen.getByTestId("ready")).toHaveTextContent("true"))
    expect(screen.getByTestId("followed")).toHaveTextContent("true")
    expect(screen.getByTestId("count")).toHaveTextContent("1")
  })

  it("treats fetch failure as no follows", async () => {
    mockedApi.fetchFollows.mockRejectedValue(new Error("boom"))

    renderProbe()

    await waitFor(() => expect(screen.getByTestId("ready")).toHaveTextContent("true"))
    expect(screen.getByTestId("followed")).toHaveTextContent("false")
  })

  it("optimistically follows and calls followTeam", async () => {
    mockedApi.fetchFollows.mockResolvedValue([])
    mockedApi.followTeam.mockResolvedValue(STL_FOLLOW)
    const user = userEvent.setup()
    renderProbe()
    await waitFor(() => expect(screen.getByTestId("ready")).toHaveTextContent("true"))

    await user.click(screen.getByText("toggle"))

    expect(screen.getByTestId("followed")).toHaveTextContent("true")
    expect(mockedApi.followTeam).toHaveBeenCalledWith("nhl", "19")
  })

  it("unfollows a followed team", async () => {
    mockedApi.fetchFollows.mockResolvedValue([STL_FOLLOW])
    mockedApi.unfollowTeam.mockResolvedValue(undefined)
    const user = userEvent.setup()
    renderProbe()
    await waitFor(() => expect(screen.getByTestId("followed")).toHaveTextContent("true"))

    await user.click(screen.getByText("toggle"))

    expect(screen.getByTestId("followed")).toHaveTextContent("false")
    expect(mockedApi.unfollowTeam).toHaveBeenCalledWith("nhl", "19")
  })

  it("rolls back the optimistic update if followTeam fails", async () => {
    mockedApi.fetchFollows.mockResolvedValue([])
    mockedApi.followTeam.mockRejectedValue(new Error("boom"))
    const user = userEvent.setup()
    renderProbe()
    await waitFor(() => expect(screen.getByTestId("ready")).toHaveTextContent("true"))

    await act(async () => {
      await user.click(screen.getByText("toggle"))
    })

    await waitFor(() => expect(screen.getByTestId("followed")).toHaveTextContent("false"))
  })
})
