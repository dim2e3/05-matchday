import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import { fetchFollows, followTeam, unfollowTeam } from "../api"
import type { League } from "../types"

function key(league: League, teamId: string): string {
  return `${league}:${teamId}`
}

interface FollowsContextValue {
  isFollowed: (league: League, teamId: string) => boolean
  toggleFollow: (league: League, teamId: string) => void
  count: number
  isReady: boolean
}

const FollowsContext = createContext<FollowsContextValue | null>(null)

export function FollowsProvider({ children }: { children: ReactNode }) {
  const [followKeys, setFollowKeys] = useState<Set<string>>(new Set())
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    fetchFollows()
      .then((follows) => {
        setFollowKeys(new Set(follows.map((f) => key(f.league, f.team_id))))
      })
      .catch(() => {
        // No follows available yet; treat as empty rather than blocking the app.
      })
      .finally(() => setIsReady(true))
  }, [])

  const isFollowed = useCallback(
    (league: League, teamId: string) => followKeys.has(key(league, teamId)),
    [followKeys],
  )

  const toggleFollow = useCallback(
    (league: League, teamId: string) => {
      const k = key(league, teamId)
      const currentlyFollowed = followKeys.has(k)

      const apply = (follow: boolean) =>
        setFollowKeys((prev) => {
          const next = new Set(prev)
          if (follow) {
            next.add(k)
          } else {
            next.delete(k)
          }
          return next
        })

      apply(!currentlyFollowed)
      const rollback = () => apply(currentlyFollowed)
      if (currentlyFollowed) {
        unfollowTeam(league, teamId).catch(rollback)
      } else {
        followTeam(league, teamId).catch(rollback)
      }
    },
    [followKeys],
  )

  const value = useMemo(
    () => ({ isFollowed, toggleFollow, count: followKeys.size, isReady }),
    [isFollowed, toggleFollow, followKeys.size, isReady],
  )

  return <FollowsContext.Provider value={value}>{children}</FollowsContext.Provider>
}

export function useFollows(): FollowsContextValue {
  const ctx = useContext(FollowsContext)
  if (!ctx) {
    throw new Error("useFollows must be used within a FollowsProvider")
  }
  return ctx
}
