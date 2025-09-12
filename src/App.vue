<template>
  <div class="wrapper wrapper--all">
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
    <MobileMenu :is-visible="mobileMenuVisible" @close="closeMobileMenu" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import SearchResults from './components/SearchResults.vue'
import MobileMenu from './components/MobileMenu.vue'
import moviesData from '../movies-data.json'

const searchQuery = ref('')
const searchResults = ref([])
const mobileMenuVisible = ref(false)

const handleSearch = (query) => {
  searchQuery.value = query
  if (query) {
    searchResults.value = moviesData.movies.filter(movie =>
      movie.id !== 'index' &&
      (movie.title || '').toLowerCase().includes(query.toLowerCase()) ||
      (movie.originalTitle || '').toLowerCase().includes(query.toLowerCase()) ||
      (movie.description || '').toLowerCase().includes(query.toLowerCase()) ||
      (movie.actors || '').toLowerCase().includes(query.toLowerCase())
    )
  } else {
    searchResults.value = []
  }
}

const clearSearch = () => {
  searchQuery.value = ''
  searchResults.value = []
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
  // Сбрасываем результаты при любой навигации
  router.afterEach(() => {
    clearSearch()
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

switchTheme()
</script>

<style>
/* Импорт существующих стилей */
@import url('./assets/lordfilm-website/css/common.css@v=h3qx6.css');
@import url('./assets/lordfilm-website/css/styles.css@v=h3qx6.css');
@import url('./assets/lordfilm-website/css/responsive.css@v=h3qx6.css');
@import url('./assets/lordfilm-website/css/engine.css@v=h3qx6.css');
@import url('./assets/lordfilm-website/css/fontawesome.css@v=h3qx6.css');
</style>
