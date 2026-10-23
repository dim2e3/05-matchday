import { useState } from "react"
import { AppTabs } from "./components/AppTabs"
import { MyGames } from "./components/MyGames"
import { Notifications } from "./components/Notifications"
import { TeamPicker } from "./components/TeamPicker"
import { TelegramConnect } from "./components/TelegramConnect"
import { FollowsProvider } from "./context/FollowsContext"
import type { Tab } from "./types"

function App() {
  const [activeTab, setActiveTab] = useState<Tab>("my-games")

  return (
    <FollowsProvider>
      <div className="app">
        <header className="app-header">
          <h1>MatchDay</h1>
          <TelegramConnect />
        </header>
        <AppTabs active={activeTab} onSelect={setActiveTab} />
        <main>
          {activeTab === "my-games" && <MyGames onFindTeams={() => setActiveTab("teams")} />}
          {activeTab === "teams" && <TeamPicker />}
          {activeTab === "notifications" && <Notifications />}
        </main>
      </div>
    </FollowsProvider>
  )
}

export default App
