import { ref, computed } from 'vue'

/**
 * Composable для работы с рейтингами страниц
 */
export function useRatings(movieId) {
  const pageLikes = ref(0)
  const pageDislikes = ref(0)
  const userVote = ref(null)

  // Вычисляемый рейтинг
  const calculatedRating = computed(() => {
    const likes = pageLikes.value
    const dislikes = pageDislikes.value
    const totalVotes = likes + dislikes

    if (totalVotes === 0) {
      return "0"
    }

    const rating = (likes / totalVotes) * 10
    return Math.round(rating)
  })

  // Загрузка рейтингов
  const loadPageRatings = async () => {
    try {
      const resp = await fetch(`/api/movie-ratings/${movieId.value}`)
      if (resp.ok) {
        const { pageLikes: likes = 0, pageDislikes: dislikes = 0 } = await resp.json()
        pageLikes.value = likes
        pageDislikes.value = dislikes
      } else {
        // Fallback к localStorage
        const savedRatings = localStorage.getItem(`page_ratings_${movieId.value}`)
        if (savedRatings) {
          const ratings = JSON.parse(savedRatings)
          pageLikes.value = ratings.likes
          pageDislikes.value = ratings.dislikes
        } else {
          // Используем начальные значения
          const { likes, dislikes } = getDefaultRatings()
          pageLikes.value = likes
          pageDislikes.value = dislikes
          localStorage.setItem(
            `page_ratings_${movieId.value}`,
            JSON.stringify({ likes, dislikes })
          )
        }
      }

      // Загружаем сохраненный голос пользователя
      const savedVote = localStorage.getItem(`page_vote_${movieId.value}`)
      if (savedVote) userVote.value = savedVote
    } catch (error) {
      console.error("Ошибка загрузки оценок:", error)
      // Fallback к localStorage
      const savedRatings = localStorage.getItem(`page_ratings_${movieId.value}`)
      if (savedRatings) {
        const ratings = JSON.parse(savedRatings)
        pageLikes.value = ratings.likes
        pageDislikes.value = ratings.dislikes
      } else {
        const { likes, dislikes } = getDefaultRatings()
        pageLikes.value = likes
        pageDislikes.value = dislikes
        localStorage.setItem(
          `page_ratings_${movieId.value}`,
          JSON.stringify({ likes, dislikes })
        )
      }
      const savedVote = localStorage.getItem(`page_vote_${movieId.value}`)
      if (savedVote) userVote.value = savedVote
    }
  }

  // Голосование за страницу
  const votePage = async (voteType) => {
    const previousVote = userVote.value
    const newVote = previousVote === voteType ? null : voteType
    
    try {
      const resp = await fetch("/api/vote-page", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          movieId: movieId.value,
          voteType: newVote,
          previousVote,
        }),
      })
      
      if (!resp.ok) throw new Error("vote API failed")
      
      const data = await resp.json()
      pageLikes.value = data.pageLikes
      pageDislikes.value = data.pageDislikes
      userVote.value = newVote

      // Сохраняем локально
      if (newVote) {
        localStorage.setItem(`page_vote_${movieId.value}`, newVote)
      } else {
        localStorage.removeItem(`page_vote_${movieId.value}`)
      }
      
      localStorage.setItem(
        `page_ratings_${movieId.value}`,
        JSON.stringify({
          likes: pageLikes.value,
          dislikes: pageDislikes.value,
        })
      )

      // Уведомляем другие вкладки
      window.dispatchEvent(
        new CustomEvent("ratings-updated", {
          detail: {
            movieId: movieId.value,
            likes: pageLikes.value,
            dislikes: pageDislikes.value,
          },
        })
      )
    } catch (error) {
      console.error("Ошибка голосования:", error)
    }
  }

  // Дефолтные рейтинги (можно настроить логику)
  const getDefaultRatings = () => {
    // Простая логика для демонстрации
    return { likes: 50, dislikes: 10 }
  }

  return {
    // State
    pageLikes,
    pageDislikes,
    userVote,
    calculatedRating,

    // Methods
    loadPageRatings,
    votePage,
  }
}
