import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { LeagueTabs } from "./LeagueTabs"

describe("LeagueTabs", () => {
  it("renders a tab for each league plus Favorites", () => {
    render(<LeagueTabs active="nfl" onSelect={vi.fn()} />)

    for (const label of ["NFL", "NBA", "NHL", "MLB", "Favorites"]) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
  })

  it("marks the active tab", () => {
    render(<LeagueTabs active="nba" onSelect={vi.fn()} />)
    expect(screen.getByText("NBA")).toHaveClass("tab-active")
    expect(screen.getByText("NFL")).not.toHaveClass("tab-active")
  })

  it("calls onSelect with the clicked tab's id", async () => {
    const onSelect = vi.fn()
    const user = userEvent.setup()

    render(<LeagueTabs active="nfl" onSelect={onSelect} />)
    await user.click(screen.getByText("Favorites"))

    expect(onSelect).toHaveBeenCalledWith("favorites")
  })
})
