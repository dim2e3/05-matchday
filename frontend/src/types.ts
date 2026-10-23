export type League = "nfl" | "nba" | "nhl" | "mlb"
export type Tab = "my-games" | "teams" | "notifications"

export type StatusState = "pre" | "in" | "post"
export type HomeAway = "home" | "away"

export interface Team {
  id: string
  name: string
  abbreviation: string
  logo: string | null
  score: string | null
  winner: boolean | null
  record: string | null
}

export interface Competitor {
  home_away: HomeAway
  team: Team
}

export interface Game {
  id: string
  start_time: string
  status_state: StatusState
  status_detail: string
  period: number | null
  clock: string | null
  competitors: Competitor[]
  venue: string | null
  league: League | null
}

export interface MyGamesResponse {
  fetched_at: string
  stale: boolean
  games: Game[]
}

export interface TeamInfo {
  id: string
  name: string
  abbreviation: string
  logo: string | null
}

export interface Follow {
  league: League
  team_id: string
  team_name: string
  abbreviation: string
  logo: string | null
  created_at: string
}

export interface Me {
  telegram_connected: boolean
  follows: number
}

export interface NotificationItem {
  kind: "kickoff" | "final"
  league: League
  text: string
  status: "pending" | "sent" | "failed"
  created_at: string
  sent_at: string | null
}
