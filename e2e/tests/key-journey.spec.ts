import { expect, test, type APIRequestContext, type Page } from "@playwright/test"

const FAKE = process.env.FAKE_ESPN_URL ?? "http://127.0.0.1:8090"
const GAME_ID = "401886427" // DAL @ STL (NHL) in the recorded fixture
// Worker poll + scoreboard cache in compose are 3 s + 2 s; give it a few cycles.
const WORKER_SETTLE_MS = 8_000

async function setGame(request: APIRequestContext, state: string, home = 0, away = 0) {
  const res = await request.post(`${FAKE}/_control/game`, {
    data: { game_id: GAME_ID, state, home_score: home, away_score: away },
  })
  expect(res.ok()).toBeTruthy()
}

async function followStl(page: Page) {
  await page.goto("/")
  await page.locator("button.tab", { hasText: "Teams" }).click()
  await page.getByRole("tab", { name: "NHL" }).click()
  await page.getByLabel("Follow St. Louis Blues").click()
  await expect(page.getByLabel("Unfollow St. Louis Blues")).toBeVisible()
  await page.locator("button.tab", { hasText: "My Games" }).click()
}

test.beforeEach(async ({ request }) => {
  await request.post(`${FAKE}/_control/reset`)
  // Let the worker record the fixture state ("pre") before a test changes it.
  await new Promise((r) => setTimeout(r, WORKER_SETTLE_MS))
})

test("S2+S3: follow a team, then see its live score update", async ({ page, request }) => {
  await followStl(page)

  const card = page.getByTestId(`game-${GAME_ID}`)
  await expect(card).toBeVisible()
  await expect(card).toContainText("St. Louis Blues")

  await setGame(request, "in", 2, 1)

  // The page polls every 15 s; the score must appear without a reload.
  await expect(card.locator(".status-badge")).toHaveText("LIVE")
  await expect(card.locator(".team-score")).toHaveText(["1", "2"]) // away, home
})

test("S4+S5+S6: connected fan gets kickoff and final on Telegram", async ({ page, request }) => {
  const chatId = Math.floor(Math.random() * 1_000_000_000)
  await followStl(page)

  // Connect Telegram: capture the deep link instead of opening Telegram.
  await page.evaluate(() => {
    ;(window as unknown as { __opened: string[] }).__opened = []
    window.open = (url?: string | URL) => {
      ;(window as unknown as { __opened: string[] }).__opened.push(String(url))
      return null
    }
  })
  await page.getByRole("button", { name: "Connect Telegram" }).click()
  const link = await expect
    .poll(() => page.evaluate(() => (window as unknown as { __opened: string[] }).__opened[0]))
    .toContain("?start=")
    .then(() => page.evaluate(() => (window as unknown as { __opened: string[] }).__opened[0]))
  const token = new URL(link).searchParams.get("start")

  // The fan presses Start in the bot; the worker picks the update up via getUpdates.
  await request.post(`${FAKE}/_control/telegram/updates`, {
    data: { chat_id: chatId, text: `/start ${token}` },
  })
  await expect
    .poll(async () => (await page.request.get("/api/me")).json())
    .toMatchObject({ telegram_connected: true })

  await setGame(request, "in", 1, 0)
  await expect
    .poll(() => messagesFor(request, chatId))
    .toContain("🟢 Kickoff: DAL @ STL (NHL)")

  await setGame(request, "post", 3, 2)
  await expect
    .poll(() => messagesFor(request, chatId))
    .toContain("🏁 Final: DAL 2 – 3 STL (NHL)")

  // Exactly once each, and visible in the history tab.
  const messages = await messagesFor(request, chatId)
  expect(messages.filter((m) => m.startsWith("🟢"))).toHaveLength(1)
  expect(messages.filter((m) => m.startsWith("🏁"))).toHaveLength(1)

  await page.reload()
  await page.locator("button.tab", { hasText: "Notifications" }).click()
  await expect(page.getByText("🏁 Final: DAL 2 – 3 STL (NHL)")).toBeVisible()
  await expect(page.getByText("Delivered").first()).toBeVisible()
})

async function messagesFor(request: APIRequestContext, chatId: number): Promise<string[]> {
  const res = await request.get(`${FAKE}/_control/telegram/messages`)
  const all = (await res.json()) as { chat_id: number; text: string }[]
  return all.filter((m) => m.chat_id === chatId).map((m) => m.text)
}
