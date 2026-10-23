import type {
  FavoriteTeam,
  FavoritesScoreboardResponse,
  League,
  ScoreboardResponse,
  Tab,
} from "./types"

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`)
  }
  const data: unknown = await res.json()
  return data as T
}

export function fetchScoreboard(
  tab: Tab,
): Promise<ScoreboardResponse | FavoritesScoreboardResponse> {
  return fetch(`/api/scoreboard/${tab}`).then((res) =>
    handleResponse<ScoreboardResponse | FavoritesScoreboardResponse>(res),
  )
}

export function fetchFavorites(): Promise<FavoriteTeam[]> {
  return fetch("/api/favorites").then((res) => handleResponse<FavoriteTeam[]>(res))
}

export function addFavorite(
  league: League,
  teamId: string,
  teamName: string,
  abbreviation: string,
): Promise<FavoriteTeam> {
  return fetch("/api/favorites", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      league,
      team_id: teamId,
      team_name: teamName,
      abbreviation,
    }),
  }).then((res) => handleResponse<FavoriteTeam>(res))
}

export async function removeFavorite(
  league: League,
  teamId: string,
): Promise<void> {
  const res = await fetch(`/api/favorites/${league}/${teamId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`)
  }
}
