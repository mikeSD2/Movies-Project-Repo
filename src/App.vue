<template>
  <div class="wrapper">
    <div class="wrapper__container layout__container--primary">
      <!-- Хедер -->
      <AppHeader @search="handleSearch" @open-mobile-menu="openMobileMenu" />
      
      <!-- Результаты поиска -->
      <SearchResults 
        v-if="searchQuery" 
        :query="searchQuery" 
        :results="searchResults"
        @close="clearSearch"
      />
      
<!-- Search Results -->
<main class="content" v-if="!searchQuery">
  <router-view />
</main>
      
      <!-- Footer -->
      <AppFooter />
    </div>
    
    <!-- Моб меню -->
    <MobileMenu 
      :is-visible="mobileMenuVisible" 
      @close="closeMobileMenu" 
      @search="handleMobileSearch" 
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import SearchResults from './components/SearchResults.vue'
import MobileMenu from './components/MobileMenu.vue'

const searchQuery = ref('')
const searchResults = ref([])
const mobileMenuVisible = ref(false)

const handleSearch = async (query) => {
  searchQuery.value = query
  if (!query) {
    searchResults.value = []
    return
  }
  const resp = await fetch(`/api/search?q=${encodeURIComponent(query)}`)
  searchResults.value = resp.ok ? await resp.json() : []
}

const clearSearch = () => {
  searchQuery.value = ''
  searchResults.value = []
}

const handleMobileSearch = (query) => {
  handleSearch(query)
  closeMobileMenu()
}

// Функции мобильного меню
const openMobileMenu = () => {
  mobileMenuVisible.value = true
}

const closeMobileMenu = () => {
  mobileMenuVisible.value = false
}

// Инициализация темы
const switchTheme = () => {
  if (typeof document === 'undefined' || typeof localStorage === 'undefined') {
    return
  }
  const bd = document.body
  const sett = ['lt', 'btn1']
  let ls = JSON.parse(localStorage.getItem('settlf'))
  bd.removeAttribute('data-theme')
  if (!ls) {
    localStorage.setItem('settlf', JSON.stringify(sett))
    bd.classList.add(sett[0], sett[1])
    if (sett[0] === 'dt') {
      bd.setAttribute('data-theme', 'dark')
    }
  } else {
    bd.classList.add(ls[0], ls[1])
    if (ls[0] === 'dt') {
      bd.setAttribute('data-theme', 'dark')
    }
  }
}

const router = useRouter()

onMounted(() => {
    const debugYM = false

  const YM = {
    hit: (url, opts = {}) => {
      try {
        // Pixel fallback удален в production

        if (window.ym && window.YM_ID) {
          window.ym(window.YM_ID, 'hit', url, opts)
        }
      } catch (e) {
        if (debugYM) console.warn('[YM] hit error', e)
      }
    },
    goal: (name, params) => {
      try {
        if (window.ym && window.YM_ID) {
          window.ym(window.YM_ID, 'reachGoal', name, params)
        }
      } catch (e) {
        if (debugYM) console.warn('[YM] goal error', e)
      }
    },
    notBounce: () => {
      try {
        if (window.ym && window.YM_ID) {
          window.ym(window.YM_ID, 'notBounce')
        }
      } catch (e) {
        if (debugYM) console.warn('[YM] notBounce error', e)
      }
    },
    verify: () => {
      try {
        if (window.ym && window.YM_ID) {
          window.ym(window.YM_ID, 'getClientID', (cid) => {
          })
        }
      } catch (e) {
        if (debugYM) console.warn('[YM] getClientID error', e)
      }
    }
  }

  // Инициализируем тему только на клиенте
  switchTheme()

  const params = new URLSearchParams(location.search);
  const q = params.get('q');
  if (q) {
    handleSearch(q);
  }

  // Сбрасываем результаты при любой навигации + отправляем hit в Я.Метрику
  // и перезапускаем трекинг вовлечённости (notBounce + цели по времени)
  // Первая загрузка страницы учитывается стандартным init метрики
  const engagement = {
    started: false,
    notBounceSent: false,
    seconds: 0,
    intervalId: null,
    goalsSent: {
      g60: false,
      g180: false,
      g300: false,
    },
    removeListeners: null,
  }

  const stopEngagement = () => {
    if (engagement.removeListeners) {
      engagement.removeListeners()
      engagement.removeListeners = null
    }
    if (engagement.intervalId) {
      clearInterval(engagement.intervalId)
      engagement.intervalId = null
    }
    engagement.started = false
    engagement.notBounceSent = false
    engagement.seconds = 0
    engagement.goalsSent = { g60: false, g180: false, g300: false }
  }

  const startEngagement = () => {
    if (engagement.started) return
    engagement.started = true
    // Считаем только видимое время на вкладке
    const tick = () => {
      if (document.hidden) return
      engagement.seconds += 1
      if (!engagement.notBounceSent && engagement.seconds >= 15) {
        YM.notBounce()
        engagement.notBounceSent = true
      }
      if (!engagement.goalsSent.g60 && engagement.seconds >= 60) {
        YM.goal('stay_60s')
        engagement.goalsSent.g60 = true
      }
      if (!engagement.goalsSent.g180 && engagement.seconds >= 180) {
        YM.goal('stay_180s')
        engagement.goalsSent.g180 = true
      }
      if (!engagement.goalsSent.g300 && engagement.seconds >= 300) {
        YM.goal('stay_300s')
        engagement.goalsSent.g300 = true
      }
    }
    engagement.intervalId = setInterval(tick, 1000)
  }

  const initEngagementTracking = () => {
    // Очистить предыдущее состояние
    stopEngagement()

    const onActivity = (e) => {
      if (debugYM) console.log('[YM] activity', e && e.type)
      startEngagement()
    }
    const onVisible = () => {
      // когда вкладка снова стала видимой — делаем мгновенный тик
      if (engagement.started && !document.hidden) {
        if (!engagement.notBounceSent && engagement.seconds >= 15) {
          YM.notBounce()
          engagement.notBounceSent = true
        }
      }
    }
    const opts = { passive: true }
    // Источники активности
    document.addEventListener('pointerdown', onActivity, opts)
    document.addEventListener('pointermove', onActivity, opts)
    document.addEventListener('mousemove', onActivity, opts)
    document.addEventListener('keydown', onActivity, opts)
    document.addEventListener('touchstart', onActivity, opts)
    document.addEventListener('touchmove', onActivity, opts)
    window.addEventListener('scroll', onActivity, opts)
    window.addEventListener('wheel', onActivity, opts)
    window.addEventListener('focus', onActivity, opts)
    document.addEventListener('visibilitychange', onVisible)

    // Если уже есть смещение прокрутки (например, по якорю) — стартуем
    if (window.scrollY > 0) {
      startEngagement()
    }

    engagement.removeListeners = () => {
      document.removeEventListener('pointerdown', onActivity, opts)
      document.removeEventListener('pointermove', onActivity, opts)
      document.removeEventListener('mousemove', onActivity, opts)
      document.removeEventListener('keydown', onActivity, opts)
      document.removeEventListener('touchstart', onActivity, opts)
      document.removeEventListener('touchmove', onActivity, opts)
      window.removeEventListener('scroll', onActivity, opts)
      window.removeEventListener('wheel', onActivity, opts)
      window.removeEventListener('focus', onActivity, opts)
      document.removeEventListener('visibilitychange', onVisible)
    }
  }

  // Инициализируем трекинг вовлеченности для первой страницы
  initEngagementTracking()

  // Я.Метрика: отправка первого hit после монтирования (на случай, если init не засчитал)
  try {
    let tries = 0
    const sendFirstHit = () => {
      if (window.__YM_FIRST_HIT_SENT__) return
      if (window.ym && window.YM_ID) {
        const url = location.pathname + location.search
        const referer = document.referrer || undefined
        YM.hit(url, { title: document.title, referer })
        window.__YM_FIRST_HIT_SENT__ = true
      } else if (tries < 10) {
        tries++
        setTimeout(sendFirstHit, 300)
      }
    }
    // подождём готовности роутера/приложения
    setTimeout(sendFirstHit, 0)
  } catch (_) {}

  router.afterEach((to, from) => {
    clearSearch()
    closeMobileMenu() // ← добавили автозакрытие мобильного меню

    try {
      if (window.ym && window.YM_ID) {
        const url = to.fullPath || (location.pathname + location.search)
        const referer = from && from.fullPath ? from.fullPath : undefined
        YM.hit(url, { title: document.title, referer })
      }
    } catch (_) {}

    // На каждую навигацию перезапускаем трекинг вовлеченности заново
    initEngagementTracking()
  })

  // Сбрасываем при клике по любой ссылке, кроме "Загрузить еще"
  const onDocClick = (e) => {
    if (!searchQuery.value) return
    const anchor = e.target.closest('a')
    if (anchor && !e.target.closest('.js-search-load-more')) {
      clearSearch()
    }
  }

  document.addEventListener('click', onDocClick)
  onBeforeUnmount(() => {
    document.removeEventListener('click', onDocClick)
  })
})

// export default {
//   setup() {
//     onMounted(() => {
//       const initYM = () => {
//         if (window.__ymLoaded) return;
//         window.__ymLoaded = true;
//         const s = document.createElement('script');
//         s.src = '/api/ym-tag.js';
//         s.async = true;
//         s.onload = () => {
//           try {
//             window.ym && window.ym(YOUR_YM_ID, 'init', {
//               clickmap: true, trackLinks: true, accurateTrackBounce: true
//             });
//           } catch {}
//         };
//         document.head.appendChild(s);
//       };
//       window.addEventListener('pointerdown', initYM, { once: true });
//       window.addEventListener('keydown', initYM,   { once: true });
//     });
//   }
// }

</script>

<style>
</style>
