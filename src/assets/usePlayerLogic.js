import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'

/**
 * Composable для работы с логикой плеера
 */
export function usePlayerLogic(movie) {
  const activeTab = ref(0)
  const isLightOff = ref(false)
  const failedPlayers = ref([])
  const allohaReadyByIndex = ref({})
  const svReadyByIndex = ref({})
  const cdnPlayerLoaded = ref(false)
  const iframeRefs = ref({})
  const svWaitStart = ref(0)

  let fallbackTimer = null

  // Конфигурация плеера
  const players = computed(() => {
    if (!movie.value || !movie.value.kinopoiskId) return []

    const allPlayers = [
      {
        name: "Плеер 1",
        type: "sv",
        kinopoiskId: movie.value.kinopoiskId,
      },
      {
        name: "Плеер 2", 
        type: "iframe",
        src: `https://polygamist-as.stloadi.live/?kp=${movie.value.kinopoiskId}&token=eb79c8a500d725f071c3bcc1e975bb`,
      },
      {
        name: "Плеер 3",
        type: "iframe", 
        src: `https://api.atomics.ws/embed/kp/${movie.value.kinopoiskId}?theme=2&theme=2`,
      },
      {
        name: "Плеер 4",
        type: "kodik",
        kinopoiskId: movie.value.kinopoiskId,
      },
    ]

    // Фильтрация для определенных стран
    const restrictedCountries = [
      "Россия", "США", "Канада", "Франция", "Великобритания", "Германия",
      "Италия", "Испания", "Бельгия", "Швеция", "Дания", "Норвегия",
      "Финляндия", "Ирландия", "Польша", "Украина", "Нидерланды",
      "Швейцария", "Австрия", "Чехия", "Венгрия", "Румыния", "Болгария",
      "Греция", "Сербия", "Хорватия", "Словения", "Словакия", "Литва",
      "Латвия", "Эстония",
    ]

    let playerList = [...allPlayers]
    const movieCountries = movie.value.country
      ? movie.value.country.split(",").map((c) => c.trim())
      : []

    const isRestricted = movieCountries.some((mc) =>
      restrictedCountries.includes(mc)
    )

    if (isRestricted) {
      playerList = playerList.filter((p) => p.type !== "kodik")
    }

    if (movie.value.youtubeId) {
      playerList.push({
        name: "Трейлер",
        type: "youtube",
        src: `https://www.youtube.com/embed/${movie.value.youtubeId}`,
      })
    }

    return playerList
  })

  // Проверка работающих плееров
  const hasWorkingPlayer = computed(() => {
    const list = players.value || []
    if (list.length === 0) return false
    return list.some((_, i) => !failedPlayers.value[i])
  })

  // Утилитарные функции
  function markPlayerFailed(index) {
    if (!failedPlayers.value[index]) {
      failedPlayers.value[index] = true
    }
  }

  function switchToNextPlayer(fromIndex) {
    for (let i = fromIndex + 1; i < players.value.length; i++) {
      if (!failedPlayers.value[i]) {
        activeTab.value = i
        return true
      }
    }
    for (let i = 0; i < fromIndex; i++) {
      if (!failedPlayers.value[i]) {
        activeTab.value = i
        return true
      }
    }
    return false
  }

  function failAndSwitch(index) {
    markPlayerFailed(index)
    switchToNextPlayer(index)
  }

  function safeFail(index) {
    if (index === activeTab.value) failAndSwitch(index)
    else markPlayerFailed(index)
  }

  function isAlloha(url) {
    try {
      return /stloadi\.live/i.test(new URL(url).hostname)
    } catch {
      return false
    }
  }

  function clearFallbackTimer() {
    if (fallbackTimer) {
      clearTimeout(fallbackTimer)
      fallbackTimer = null
    }
  }

  function registerIframeRef(index, el) {
    if (!el) {
      delete iframeRefs.value[index]
      return
    }
    iframeRefs.value[index] = el
  }

  // Проверка плеера через API
  async function probePlayer(url) {
    try {
      const r = await fetch("/api/probe-player?url=" + encodeURIComponent(url))
      const j = await r.json()
      return j
    } catch {
      return { ok: null, status: 0, matched: false }
    }
  }

  // Обработчики событий iframe
  async function handleIframeLoad(index) {
    if (activeTab.value !== index) return
    const p = players.value[index]
    if (!p || p.type !== "iframe") return

    if (isAlloha(p.src)) {
      return // Обрабатывается отдельно
    }

    const res = await probePlayer(p.src)
    if (activeTab.value !== index) return
    if (res && res.ok === true) clearFallbackTimer()
    else failAndSwitch(index)
  }

  function handleIframeError(index) {
    if (activeTab.value !== index) return
    const p = players.value[index]
    if (p && p.type === "iframe" && isAlloha(p.src)) {
      probePlayer(p.src)
        .then((res) => {
          if (activeTab.value !== index) return
          if (res && res.matched === true) failAndSwitch(index)
          else clearFallbackTimer()
        })
        .catch(() => {
          clearFallbackTimer()
        })
      return
    }
    failAndSwitch(index)
  }

  // Watchers
  watch(
    players,
    (list) => {
      failedPlayers.value = Array(list.length).fill(false)
    },
    { immediate: true }
  )

  // Обработка Light Off
  watch(isLightOff, (newValue) => {
    if (typeof document === "undefined") return
    const playerContainer = document.getElementById("player-container")
    if (newValue) {
      document.body.classList.add("light-off")
      if (playerContainer) {
        playerContainer.scrollIntoView({ behavior: "smooth", block: "center" })
      }
    } else {
      document.body.classList.remove("light-off")
    }
  })

  // Cleanup
  onBeforeUnmount(() => {
    clearFallbackTimer()
  })

  return {
    // State
    activeTab,
    isLightOff,
    failedPlayers,
    players,
    hasWorkingPlayer,
    cdnPlayerLoaded,
    
    // Methods
    markPlayerFailed,
    switchToNextPlayer,
    failAndSwitch,
    safeFail,
    isAlloha,
    clearFallbackTimer,
    registerIframeRef,
    probePlayer,
    handleIframeLoad,
    handleIframeError,
  }
}
