import { useFavorites } from "../context/FavoritesContext"
import type { League } from "../types"

interface FavoriteStarProps {
  league: League
  teamId: string
  teamName: string
  abbreviation: string
}

export function FavoriteStar({
  league,
  teamId,
  teamName,
  abbreviation,
}: FavoriteStarProps) {
  const { isFavorite, toggleFavorite } = useFavorites()
  const favorite = isFavorite(league, teamId)

  return (
    <button
      className="favorite-star"
      aria-label={favorite ? `Unfavorite ${teamName}` : `Favorite ${teamName}`}
      aria-pressed={favorite}
      onClick={(e) => {
        e.stopPropagation()
        toggleFavorite(league, teamId, teamName, abbreviation)
      }}
    >
      {favorite ? "★" : "☆"}
    </button>
  )
}
