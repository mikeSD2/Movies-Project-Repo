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

</script>

<style>
</style>
