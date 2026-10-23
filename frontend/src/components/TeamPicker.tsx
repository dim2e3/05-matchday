import { useEffect, useState } from "react"
import { fetchTeams } from "../api"
import { useFollows } from "../context/FollowsContext"
import type { League, TeamInfo } from "../types"
import { ErrorBanner } from "./ErrorBanner"
import { FollowStar } from "./FollowStar"

const LEAGUES: { id: League; label: string }[] = [
  { id: "nfl", label: "NFL" },
  { id: "nba", label: "NBA" },
  { id: "nhl", label: "NHL" },
  { id: "mlb", label: "MLB" },
]

export function TeamPicker() {
  const [league, setLeague] = useState<League>("nfl")
  const [teams, setTeams] = useState<TeamInfo[] | null>(null)
  const [error, setError] = useState(false)
  const [query, setQuery] = useState("")
  const { isFollowed } = useFollows()

  useEffect(() => {
    let cancelled = false
    setTeams(null)
    setError(false)
    fetchTeams(league)
      .then((result) => !cancelled && setTeams(result))
      .catch(() => !cancelled && setError(true))
    return () => {
      cancelled = true
    }
  }, [league])

  const q = query.trim().toLowerCase()
  const visible = (teams ?? [])
    .filter(
      (t) => !q || t.name.toLowerCase().includes(q) || t.abbreviation.toLowerCase() === q,
    )
    // Followed teams first, then alphabetical (the API already sorts by name).
    .sort((a, b) => Number(isFollowed(league, b.id)) - Number(isFollowed(league, a.id)))

  return (
    <div className="team-picker">
      <div className="chips" role="tablist" aria-label="League">
        {LEAGUES.map((l) => (
          <button
            key={l.id}
            role="tab"
            aria-selected={l.id === league}
            className={l.id === league ? "chip chip-active" : "chip"}
            onClick={() => setLeague(l.id)}
          >
            {l.label}
          </button>
        ))}
      </div>
      <input
        className="search"
        type="search"
        placeholder="Search teams"
        aria-label="Search teams"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      {error && <ErrorBanner message="Couldn't load teams. Try again in a moment." />}
      {!teams && !error && <div className="status-text">Loading teams…</div>}
      <ul className="team-list">
        {visible.map((team) => (
          <li key={team.id} className="team-row">
            {team.logo && <img className="team-logo" src={team.logo} alt="" width={24} height={24} />}
            <span className="team-name">{team.name}</span>
            <FollowStar league={league} teamId={team.id} teamName={team.name} />
          </li>
        ))}
      </ul>
      {teams && visible.length === 0 && <div className="status-text">No teams match.</div>}
    </div>
  )
}
