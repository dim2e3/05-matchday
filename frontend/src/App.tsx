import { useState } from "react"
import { LeagueTabs } from "./components/LeagueTabs"
import { Scoreboard } from "./components/Scoreboard"
import { FavoritesProvider } from "./context/FavoritesContext"
import type { Tab } from "./types"

function App() {
  const [activeTab, setActiveTab] = useState<Tab>("nfl")

  return (
    <FavoritesProvider>
      <div className="app">
        <header className="app-header">
          <h1>ScoreFeed</h1>
        </header>
        <LeagueTabs active={activeTab} onSelect={setActiveTab} />
        <main>
          <Scoreboard tab={activeTab} />
        </main>
      </div>
    </FavoritesProvider>
  )
}

export default App
