import { useFollows } from "../context/FollowsContext"
import type { League } from "../types"

interface FollowStarProps {
  league: League
  teamId: string
  teamName: string
}

export function FollowStar({ league, teamId, teamName }: FollowStarProps) {
  const { isFollowed, toggleFollow } = useFollows()
  const followed = isFollowed(league, teamId)

  return (
    <button
      className="follow-star"
      aria-label={followed ? `Unfollow ${teamName}` : `Follow ${teamName}`}
      aria-pressed={followed}
      onClick={(e) => {
        e.stopPropagation()
        toggleFollow(league, teamId)
      }}
    >
      {followed ? "★" : "☆"}
    </button>
  )
}
