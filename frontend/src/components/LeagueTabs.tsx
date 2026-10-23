import type { Tab } from "../types"

const TABS: { id: Tab; label: string }[] = [
  { id: "nfl", label: "NFL" },
  { id: "nba", label: "NBA" },
  { id: "nhl", label: "NHL" },
  { id: "mlb", label: "MLB" },
  { id: "favorites", label: "Favorites" },
]

interface LeagueTabsProps {
  active: Tab
  onSelect: (tab: Tab) => void
}

export function LeagueTabs({ active, onSelect }: LeagueTabsProps) {
  return (
    <nav className="league-tabs">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          className={tab.id === active ? "tab tab-active" : "tab"}
          onClick={() => onSelect(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  )
}
