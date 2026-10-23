import type { Game } from "../types"
import { FollowStar } from "./FollowStar"
import { StatusBadge } from "./StatusBadge"

interface GameCardProps {
  game: Game
  showLeagueBadge?: boolean
}

function formatStartTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    weekday: "short",
    hour: "numeric",
    minute: "2-digit",
  })
}

export function GameCard({ game, showLeagueBadge = false }: GameCardProps) {
  const away = game.competitors.find((c) => c.home_away === "away")
  const home = game.competitors.find((c) => c.home_away === "home")
  const league = game.league

  return (
    <div className="game-card" data-testid={`game-${game.id}`}>
      <div className="game-card-header">
        {showLeagueBadge && league && (
          <span className="league-badge">{league.toUpperCase()}</span>
        )}
        <StatusBadge state={game.status_state} detail={game.status_detail} />
        {game.status_state !== "pre" && (
          <span className="game-detail">
            {game.status_detail}
            {game.clock && game.status_state === "in" ? ` · ${game.clock}` : ""}
          </span>
        )}
        {game.status_state === "pre" && (
          <span className="game-detail">{formatStartTime(game.start_time)}</span>
        )}
      </div>

      {[away, home].map((competitor) =>
        competitor ? (
          <div key={competitor.team.id} className="team-row">
            {competitor.team.logo && (
              <img
                className="team-logo"
                src={competitor.team.logo}
                alt=""
                width={24}
                height={24}
              />
            )}
            {league && (
              <FollowStar
                league={league}
                teamId={competitor.team.id}
                teamName={competitor.team.name}
              />
            )}
            <span className="team-name">{competitor.team.name}</span>
            {competitor.team.record && (
              <span className="team-record">{competitor.team.record}</span>
            )}
            <span className="team-score">{competitor.team.score ?? "-"}</span>
          </div>
        ) : null,
      )}

      {game.venue && <div className="game-venue">{game.venue}</div>}
    </div>
  )
}
