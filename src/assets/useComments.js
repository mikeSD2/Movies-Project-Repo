import { ref, computed, nextTick } from 'vue'

/**
 * Composable для работы с комментариями
 */
export function useComments(movieId) {
  const comments = ref([])
  const commentsCount = ref(0)
  const replyToCommentId = ref(null)
  const commentForm = ref({
    name: "",
    email: "",
    comment: "",
  })
  const showCaptcha = ref(false)

  // Обработанные комментарии с уровнями вложенности
  const processedComments = computed(() => {
    const commentMap = {}
    comments.value.forEach((comment) => {
      commentMap[comment.id] = { ...comment, children: [] }
    })

    const result = []
    comments.value.forEach((comment) => {
      if (comment.parentId && commentMap[comment.parentId]) {
        commentMap[comment.parentId].children.push(commentMap[comment.id])
      } else {
        result.push(commentMap[comment.id])
      }
    })

    const flatten = (comments, level = 0) => {
      let flatList = []
      comments.forEach((comment) => {
        flatList.push({ ...comment, level })
        if (comment.children.length) {
          flatList = flatList.concat(flatten(comment.children, level + 1))
        }
      })
      return flatList
    }

    return flatten(result)
  })

  // Загрузка комментариев
  const loadComments = async () => {
    try {
      const response = await fetch(`/api/movie-comments/${movieId.value}`)

      if (response.ok) {
        const result = await response.json()
        comments.value = result.comments || []
        commentsCount.value = comments.value.length
      } else {
        console.error("Ошибка загрузки комментариев с сервера")
        comments.value = []
        commentsCount.value = 0
      }
    } catch (error) {
      console.error("Ошибка загрузки комментариев:", error)
      comments.value = []
      commentsCount.value = 0
    }
  }

  // Отправка комментария
  const submitComment = async () => {
    try {
      if (!commentForm.value.comment || commentForm.value.comment.length < 50) {
        alert("Комментарий должен содержать минимум 50 знаков")
        return
      }

      // Проверяем reCAPTCHA
      let token = null
      if (window.grecaptcha) {
        token = window.grecaptcha.getResponse()
        if (!token) {
          alert("Пожалуйста, подтвердите, что вы не робот.")
          return
        }
      }

      const requestBody = {
        movieId: movieId.value,
        name: commentForm.value.name || "Гость",
        email: commentForm.value.email,
        comment: commentForm.value.comment,
        "g-recaptcha-response": token,
        parentId: replyToCommentId.value,
      }

      const response = await fetch("/api/add-comment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        throw new Error("Ошибка сервера при сохранении комментария")
      }

      const result = await response.json()
      console.log("Комментарий успешно сохранен:", result)

      // Очищаем форму
      commentForm.value.comment = ""
      commentForm.value.name = ""
      commentForm.value.email = ""
      showCaptcha.value = false
      replyToCommentId.value = null

      // Сбрасываем reCAPTCHA
      if (window.grecaptcha) {
        window.grecaptcha.reset()
      }

      // Перезагружаем комментарии
      await loadComments()
    } catch (error) {
      console.error("Ошибка отправки комментария:", error)
      alert("Ошибка при отправке комментария. " + error.message)
    }
  }

  // Голосование за комментарий
  const voteComment = async (commentId, voteType) => {
    try {
      const comment = comments.value.find((c) => c.id === commentId)
      if (!comment) return

      const voteKey = `comment_vote_${movieId.value}_${commentId}`
      const previousVote = localStorage.getItem(voteKey)
      const newVote = previousVote === voteType ? null : voteType

      // Обновляем рейтинг локально
      if (previousVote === "like") comment.rating--
      if (previousVote === "dislike") comment.rating++
      if (newVote === "like") comment.rating++
      if (newVote === "dislike") comment.rating--

      // Сохраняем в localStorage
      if (newVote) {
        localStorage.setItem(voteKey, newVote)
      } else {
        localStorage.removeItem(voteKey)
      }

      // Сохраняем на сервере
      try {
        const response = await fetch("/api/vote-comment", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            movieId: movieId.value,
            commentId: commentId,
            voteType: newVote,
            previousVote: previousVote,
          }),
        })

        if (!response.ok) {
          throw new Error("Ошибка сервера при сохранении голоса")
        }

        const result = await response.json()
        comment.rating = result.comment.rating
      } catch (apiError) {
        console.error("Ошибка API при сохранении голоса:", apiError)
        // Откатываем изменения при ошибке
        if (previousVote === "like") comment.rating--
        if (previousVote === "dislike") comment.rating++
        if (voteType === "like") comment.rating++
        if (voteType === "dislike") comment.rating--
        
        alert("Ошибка при сохранении голоса. Попробуйте еще раз.")
      }
    } catch (error) {
      console.error("Ошибка голосования за комментарий:", error)
    }
  }

  // Получение голоса пользователя
  const getUserVote = (commentId) => {
    const voteKey = `comment_vote_${movieId.value}_${commentId}`
    return localStorage.getItem(voteKey)
  }

  // Ответ на комментарий
  const replyTo = (commentId) => {
    replyToCommentId.value = commentId
  }

  // Отмена ответа
  const cancelReply = () => {
    replyToCommentId.value = null
  }

  // Показ капчи при фокусе
  const showCaptchaOnFocus = async () => {
    showCaptcha.value = true
    await nextTick()

    const recaptchaContainer = document.querySelector(".g-recaptcha")
    if (recaptchaContainer && window.grecaptcha) {
      try {
        window.grecaptcha.reset()
      } catch (error) {
        console.log("reCAPTCHA reset error:", error)
        await recreateRecaptcha()
      }
    } else if (window.grecaptcha) {
      await recreateRecaptcha()
    } else {
      console.log("reCAPTCHA не загружен, ждем...")
      await waitForRecaptcha()
      await recreateRecaptcha()
    }
  }

  // Пересоздание reCAPTCHA
  const recreateRecaptcha = async () => {
    try {
      const oldContainer = document.querySelector(".g-recaptcha")
      if (oldContainer) {
        oldContainer.remove()
      }

      const recaptchaDiv = document.createElement("div")
      recaptchaDiv.className = "g-recaptcha"
      recaptchaDiv.setAttribute("data-sitekey", "6LeMNBgsAAAAAF-cI33csG6ZC9_BKo6x-ljo7yZN")
      recaptchaDiv.setAttribute("data-theme", "light")
      recaptchaDiv.setAttribute("data-language", "ru")

      const recaptchaContainer = document.querySelector(".form__row--protect")
      if (recaptchaContainer) {
        recaptchaContainer.appendChild(recaptchaDiv)
        window.grecaptcha.render(recaptchaDiv, {
          sitekey: "6LeMNBgsAAAAAF-cI33csG6ZC9_BKo6x-ljo7yZN",
          theme: "light",
          language: "ru",
        })
      }
    } catch (error) {
      console.error("Ошибка инициализации reCAPTCHA:", error)
    }
  }

  // Ожидание загрузки reCAPTCHA
  const waitForRecaptcha = () => {
    return new Promise((resolve) => {
      if (window.grecaptcha) {
        resolve()
        return
      }

      const checkInterval = setInterval(() => {
        if (window.grecaptcha) {
          clearInterval(checkInterval)
          resolve()
        }
      }, 100)

      setTimeout(() => {
        clearInterval(checkInterval)
        resolve()
      }, 5000)
    })
  }

  return {
    // State
    comments,
    commentsCount,
    replyToCommentId,
    commentForm,
    showCaptcha,
    processedComments,

    // Methods
    loadComments,
    submitComment,
    voteComment,
    getUserVote,
    replyTo,
    cancelReply,
    showCaptchaOnFocus,
  }
}
