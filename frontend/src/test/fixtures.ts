import type { Game } from "../types"

export function makeGame(overrides: Partial<Game> = {}): Game {
  return {
    id: "1",
    start_time: "2026-09-12T18:00:00Z",
    status_state: "in",
    status_detail: "Q3 4:12",
    period: 3,
    clock: "4:12",
    venue: "Test Stadium",
    league: "nfl",
    competitors: [
      {
        home_away: "away",
        team: {
          id: "17",
          name: "New England Patriots",
          abbreviation: "NE",
          logo: null,
          score: "10",
          winner: null,
          record: "0-1",
        },
      },
      {
        home_away: "home",
        team: {
          id: "26",
          name: "Seattle Seahawks",
          abbreviation: "SEA",
          logo: null,
          score: "13",
          winner: null,
          record: "1-0",
        },
      },
    ],
    ...overrides,
  }
}
