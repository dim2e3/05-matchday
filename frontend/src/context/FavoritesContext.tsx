import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import { addFavorite, fetchFavorites, removeFavorite } from "../api"
import type { League } from "../types"

function key(league: League, teamId: string): string {
  return `${league}:${teamId}`
}

interface FavoritesContextValue {
  isFavorite: (league: League, teamId: string) => boolean
  toggleFavorite: (
    league: League,
    teamId: string,
    teamName: string,
    abbreviation: string,
  ) => void
  isReady: boolean
}

const FavoritesContext = createContext<FavoritesContextValue | null>(null)

export function FavoritesProvider({ children }: { children: ReactNode }) {
  const [favoriteKeys, setFavoriteKeys] = useState<Set<string>>(new Set())
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    fetchFavorites()
      .then((favorites) => {
        setFavoriteKeys(new Set(favorites.map((f) => key(f.league, f.team_id))))
      })
      .catch(() => {
        // No favorites available yet; treat as empty rather than blocking the app.
      })
      .finally(() => setIsReady(true))
  }, [])

  const isFavorite = useCallback(
    (league: League, teamId: string) => favoriteKeys.has(key(league, teamId)),
    [favoriteKeys],
  )

  const toggleFavorite = useCallback(
    (league: League, teamId: string, teamName: string, abbreviation: string) => {
      const k = key(league, teamId)
      const currentlyFavorite = favoriteKeys.has(k)

      setFavoriteKeys((prev) => {
        const next = new Set(prev)
        if (currentlyFavorite) {
          next.delete(k)
        } else {
          next.add(k)
        }
        return next
      })

      const rollback = () => {
        setFavoriteKeys((prev) => {
          const next = new Set(prev)
          if (currentlyFavorite) {
            next.add(k)
          } else {
            next.delete(k)
          }
          return next
        })
      }

      if (currentlyFavorite) {
        removeFavorite(league, teamId).catch(rollback)
      } else {
        addFavorite(league, teamId, teamName, abbreviation).catch(rollback)
      }
    },
    [favoriteKeys],
  )

  const value = useMemo(
    () => ({ isFavorite, toggleFavorite, isReady }),
    [isFavorite, toggleFavorite, isReady],
  )

  return (
    <FavoritesContext.Provider value={value}>
      {children}
    </FavoritesContext.Provider>
  )
}

export function useFavorites(): FavoritesContextValue {
  const ctx = useContext(FavoritesContext)
  if (!ctx) {
    throw new Error("useFavorites must be used within a FavoritesProvider")
  }
  return ctx
}
