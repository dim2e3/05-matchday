import type { Tab } from "../types"

const TABS: { id: Tab; label: string }[] = [
  { id: "my-games", label: "My Games" },
  { id: "teams", label: "Teams" },
  { id: "notifications", label: "Notifications" },
]

interface AppTabsProps {
  active: Tab
  onSelect: (tab: Tab) => void
}

export function AppTabs({ active, onSelect }: AppTabsProps) {
  return (
    <nav className="tabs" aria-label="Sections">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          className={tab.id === active ? "tab tab-active" : "tab"}
          aria-current={tab.id === active ? "page" : undefined}
          onClick={() => onSelect(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  )
}
