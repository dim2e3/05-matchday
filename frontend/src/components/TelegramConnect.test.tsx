import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"
import * as api from "../api"
import { TelegramConnect } from "./TelegramConnect"

vi.mock("../api")
const mockedApi = vi.mocked(api)

describe("TelegramConnect", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(window, "open").mockImplementation(() => null)
  })

  it("S4: Connect opens the bot deep link", async () => {
    mockedApi.fetchMe.mockResolvedValue({ telegram_connected: false, follows: 0 })
    mockedApi.createTelegramLink.mockResolvedValue({
      url: "https://t.me/matchday_alerts_bot?start=abc",
    })
    const user = userEvent.setup()

    render(<TelegramConnect />)
    await user.click(await screen.findByText("Connect Telegram"))

    expect(window.open).toHaveBeenCalledWith(
      "https://t.me/matchday_alerts_bot?start=abc",
      "_blank",
      "noopener",
    )
  })

  it("S4: connected users can disconnect", async () => {
    mockedApi.fetchMe.mockResolvedValue({ telegram_connected: true, follows: 1 })
    mockedApi.disconnectTelegram.mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(<TelegramConnect />)
    expect(await screen.findByText("✅ Telegram connected")).toBeInTheDocument()
    await user.click(screen.getByText("Disconnect"))

    expect(await screen.findByText("Connect Telegram")).toBeInTheDocument()
    expect(mockedApi.disconnectTelegram).toHaveBeenCalled()
  })

  it("S4: shows an error when the link cannot be created", async () => {
    mockedApi.fetchMe.mockResolvedValue({ telegram_connected: false, follows: 0 })
    mockedApi.createTelegramLink.mockRejectedValue(new api.ApiError(500))
    const user = userEvent.setup()

    render(<TelegramConnect />)
    await user.click(await screen.findByText("Connect Telegram"))

    expect(await screen.findByText("Something went wrong, try again.")).toBeInTheDocument()
  })
})
