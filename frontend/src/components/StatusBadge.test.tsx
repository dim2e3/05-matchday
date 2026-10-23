import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { StatusBadge } from "./StatusBadge"

describe("StatusBadge", () => {
  it("shows LIVE for in-progress games", () => {
    render(<StatusBadge state="in" detail="Q3 4:12" />)
    expect(screen.getByText("LIVE")).toBeInTheDocument()
  })

  it("shows FINAL for completed games", () => {
    render(<StatusBadge state="post" detail="Final" />)
    expect(screen.getByText("FINAL")).toBeInTheDocument()
  })

  it("shows the scheduled detail text for upcoming games", () => {
    render(<StatusBadge state="pre" detail="9/13 - 1:00 PM EDT" />)
    expect(screen.getByText("9/13 - 1:00 PM EDT")).toBeInTheDocument()
  })
})
