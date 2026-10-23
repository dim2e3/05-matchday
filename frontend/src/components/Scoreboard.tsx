import { fetchScoreboard } from "../api"
import { usePolling } from "../hooks/usePolling"
import type {
  FavoritesScoreboardResponse,
  ScoreboardResponse,
  Tab,
} from "../types"
import { ErrorBanner } from "./ErrorBanner"
import { GameCard } from "./GameCard"

const POLL_INTERVAL_MS = 20_000

interface ScoreboardProps {
  tab: Tab
}

export function Scoreboard({ tab }: ScoreboardProps) {
  const { data, error, isLoading } = usePolling<
    ScoreboardResponse | FavoritesScoreboardResponse
  >(() => fetchScoreboard(tab), POLL_INTERVAL_MS, [tab])

  const isFavorites = tab === "favorites"
  const stale = "stale" in (data ?? {}) && (data as ScoreboardResponse).stale

  if (isLoading) {
    return <div className="scoreboard-status">Loading {tab} scores…</div>
  }

  if (error && !data) {
    return (
      <div className="scoreboard-status">
        <ErrorBanner message={`Couldn't load ${tab} scores. Retrying…`} />
      </div>
    )
  }

  const games = data?.games ?? []

  return (
    <div className="scoreboard">
      {error && data && (
        <ErrorBanner message="Live updates unavailable, showing last known scores." />
      )}
      {!error && stale && (
        <ErrorBanner message="Showing last known scores, live updates temporarily unavailable." />
      )}
      {games.length === 0 && (
        <div className="scoreboard-status">
          {isFavorites
            ? "Star a team to see their games here."
            : "No games today."}
        </div>
      )}
      <div className="game-list">
        {games.map((game) => (
          <GameCard key={game.id} game={game} showLeagueBadge={isFavorites} />
        ))}
      </div>
    </div>
  )
}
