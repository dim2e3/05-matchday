import { fetchMyGames } from "../api"
import { useFollows } from "../context/FollowsContext"
import { usePolling } from "../hooks/usePolling"
import type { MyGamesResponse } from "../types"
import { ErrorBanner } from "./ErrorBanner"
import { GameCard } from "./GameCard"

export const POLL_INTERVAL_MS = 15_000

interface MyGamesProps {
  onFindTeams: () => void
}

export function MyGames({ onFindTeams }: MyGamesProps) {
  const { count } = useFollows()
  const { data, error, isLoading } = usePolling<MyGamesResponse>(
    fetchMyGames,
    POLL_INTERVAL_MS,
    [count],
  )

  if (isLoading) {
    return <div className="status-text">Loading your games…</div>
  }

  if (error && !data) {
    return (
      <div className="status-text">
        <ErrorBanner message="Couldn't load live scores. Retrying…" />
      </div>
    )
  }

  const games = data?.games ?? []

  return (
    <div className="my-games">
      {error && data && (
        <ErrorBanner message="Live updates unavailable, showing last known scores." />
      )}
      {!error && data?.stale && (
        <ErrorBanner message="Scores may be out of date — live updates are temporarily unavailable." />
      )}
      {games.length === 0 &&
        (count === 0 ? (
          <div className="status-text">
            <p>Follow a team to see their games here.</p>
            <button className="primary" onClick={onFindTeams}>
              Find teams
            </button>
          </div>
        ) : (
          <div className="status-text">No games today for the teams you follow.</div>
        ))}
      <div className="game-list">
        {games.map((game) => (
          <GameCard key={game.id} game={game} showLeagueBadge />
        ))}
      </div>
    </div>
  )
}
