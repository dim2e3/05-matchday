import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { AppTabs } from "./AppTabs"

describe("AppTabs", () => {
  it("renders the three sections", () => {
    render(<AppTabs active="my-games" onSelect={vi.fn()} />)

    for (const label of ["My Games", "Teams", "Notifications"]) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
  })

  it("marks the active tab", () => {
    render(<AppTabs active="teams" onSelect={vi.fn()} />)
    expect(screen.getByText("Teams")).toHaveClass("tab-active")
    expect(screen.getByText("My Games")).not.toHaveClass("tab-active")
  })

  it("calls onSelect with the clicked tab's id", async () => {
    const onSelect = vi.fn()
    const user = userEvent.setup()

    render(<AppTabs active="my-games" onSelect={onSelect} />)
    await user.click(screen.getByText("Notifications"))

    expect(onSelect).toHaveBeenCalledWith("notifications")
  })
})
