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
      
<!-- Основной контент -->
<main class="content" v-if="!searchQuery">
  <router-view />
</main>
      
      <!-- Футер -->
      <AppFooter />
    </div>
    
    <!-- Мобильное меню -->
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
    timers: [],
    removeListeners: null,
  }

  const stopEngagement = () => {
    if (engagement.removeListeners) {
      engagement.removeListeners()
      engagement.removeListeners = null
    }
    engagement.timers.forEach((t) => clearTimeout(t))
    engagement.timers = []
    engagement.started = false
    engagement.notBounceSent = false
  }

  const startEngagement = () => {
    // Запустить отслеживание вовлеченности при первом признаке активности пользователя
    if (engagement.started) return
    engagement.started = true

    // Через 15с после первой активности — помечаем неотказ
    const t1 = setTimeout(() => {
      try {
        if (!engagement.notBounceSent && window.ym && window.YM_ID) {
          if (window.__YM_DEBUG) console.debug('[YM] notBounce')
          window.ym(window.YM_ID, 'notBounce')
          engagement.notBounceSent = true
        }
      } catch (_) {}
    }, 15000)
    engagement.timers.push(t1)

    // Мягкие цели времени нахождения на странице (после начала активности)
    const scheduleGoal = (ms, name) => {
      const tid = setTimeout(() => {
        try {
          if (window.__YM_DEBUG) console.debug('[YM] goal', name)
          window.ym && window.YM_ID && window.ym(window.YM_ID, 'reachGoal', name)
        } catch (_) {}
      }, ms)
      engagement.timers.push(tid)
    }
    scheduleGoal(60000, 'stay_60s')
    scheduleGoal(180000, 'stay_180s')
    scheduleGoal(300000, 'stay_300s')
  }

  const initEngagementTracking = () => {
    // Очистить предыдущее состояние
    stopEngagement()

    const onActivity = () => {
      startEngagement()
    }
    const opts = { passive: true }
    document.addEventListener('scroll', onActivity, opts)
    document.addEventListener('pointerdown', onActivity, opts)
    document.addEventListener('keydown', onActivity, opts)

    engagement.removeListeners = () => {
      document.removeEventListener('scroll', onActivity, opts)
      document.removeEventListener('pointerdown', onActivity, opts)
      document.removeEventListener('keydown', onActivity, opts)
    }
  }

  // Инициализируем трекинг вовлеченности для первой страницы
  initEngagementTracking()

  router.afterEach((to, from) => {
    clearSearch()
    closeMobileMenu() // ← добавили автозакрытие мобильного меню

    try {
      if (window.ym && window.YM_ID) {
        const url = to.fullPath || (location.pathname + location.search)
        const referer = from && from.fullPath ? from.fullPath : undefined
        if (window.__YM_DEBUG) console.debug('[YM] hit', url, { title: document.title, referer })
        ym(window.YM_ID, 'hit', url, {
          title: document.title,
          referer
        })
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
