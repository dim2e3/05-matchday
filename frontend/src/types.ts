export type League = "nfl" | "nba" | "nhl" | "mlb"
export type Tab = League | "favorites"

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

export interface ScoreboardResponse {
  league: League
  fetched_at: string
  stale: boolean
  games: Game[]
}

export interface FavoritesScoreboardResponse {
  fetched_at: string
  games: Game[]
}

export interface FavoriteTeam {
  league: League
  team_id: string
  team_name: string
  abbreviation: string
  added_at: string
}
