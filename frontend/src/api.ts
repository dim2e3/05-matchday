import type {
  Follow,
  League,
  Me,
  MyGamesResponse,
  NotificationItem,
  TeamInfo,
} from "./types"

export class ApiError extends Error {
  status: number

  constructor(status: number) {
    super(`Request failed: ${status}`)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { credentials: "same-origin", ...init })
  if (!res.ok) {
    throw new ApiError(res.status)
  }
  if (res.status === 204) {
    return undefined as T
  }
  const data: unknown = await res.json()
  return data as T
}

export function fetchMyGames(): Promise<MyGamesResponse> {
  return request<MyGamesResponse>("/api/my-games")
}

export function fetchTeams(league: League): Promise<TeamInfo[]> {
  return request<TeamInfo[]>(`/api/teams/${league}`)
}

export function fetchFollows(): Promise<Follow[]> {
  return request<Follow[]>("/api/follows")
}

export function followTeam(league: League, teamId: string): Promise<Follow> {
  return request<Follow>("/api/follows", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ league, team_id: teamId }),
  })
}

export function unfollowTeam(league: League, teamId: string): Promise<void> {
  return request<void>(`/api/follows/${league}/${teamId}`, { method: "DELETE" })
}

export function fetchMe(): Promise<Me> {
  return request<Me>("/api/me")
}

export function createTelegramLink(): Promise<{ url: string }> {
  return request<{ url: string }>("/api/telegram/link", { method: "POST" })
}

export function disconnectTelegram(): Promise<void> {
  return request<void>("/api/telegram/link", { method: "DELETE" })
}

export function fetchNotifications(): Promise<NotificationItem[]> {
  return request<NotificationItem[]>("/api/notifications")
}
