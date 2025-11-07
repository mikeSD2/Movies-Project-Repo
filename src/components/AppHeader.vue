<template>
  <header class="header d-flex ai-center r-gap-10 c-gap-10 anim" id="header">
    <router-link to="/" class="nav-bar___logo logo">
      Prosmotr<span>Zone</span>
    </router-link>
    
    <ul class="nav-bar___nav d-flex c-gap-20 js-this-in-mobile-menu">
      <li>
        <a href="#" @click.prevent>Фильмы</a>
        <div class="nav-bar___nav-hidden anim">
          <ul class="nav-bar___nav-hidden-col">
            <li><router-link to="/filmy">Все</router-link></li>
            <li>По году:</li>
            <li><router-link to="/filmy?year=2025">2025</router-link></li>
            <li><router-link to="/filmy?year=2024">2024</router-link></li>
            <li><router-link to="/filmy?year=2023">2023</router-link></li>
          </ul>
          <ul class="nav-bar___nav-hidden-col">
            <li>По жанрам:</li>
            <li><router-link to="/filmy?genre=Биография">Биографические</router-link></li>
            <li><router-link to="/filmy?genre=Вестерн">Вестерны</router-link></li>
            <li><router-link to="/filmy?genre=Военный">Военные</router-link></li>
            <li><router-link to="/filmy?genre=Боевик">Боевики</router-link></li>
            <li><router-link to="/filmy?genre=Драма">Драмы</router-link></li>
            <li><router-link to="/filmy?genre=История">Исторические</router-link></li>
            <li><router-link to="/filmy?genre=Документальный">Документальные</router-link></li>
            <li><router-link to="/filmy?genre=Детектив">Детективы</router-link></li>
            <li><router-link to="/filmy?genre=Семейный">Детские</router-link></li>
            <li><router-link to="/filmy?genre=Комедия">Комедии</router-link></li>
          </ul>
          <ul class="nav-bar___nav-hidden-col">
            <li><router-link to="/filmy?genre=Фэнтези">Фэнтези</router-link></li>
            <li><router-link to="/filmy?genre=Криминал">Криминал</router-link></li>
            <li><router-link to="/filmy?genre=Спорт">Спорт</router-link></li>
            <li><router-link to="/filmy?genre=Триллер">Триллеры</router-link></li>
            <li><router-link to="/filmy?genre=Мелодрама">Мелодрамы</router-link></li>
            <li><router-link to="/filmy?genre=Приключения">Приключения</router-link></li>
            <li><router-link to="/filmy?genre=Фантастика">Фантастика</router-link></li>
            <li><router-link to="/filmy?genre=Семейный">Семейные</router-link></li>
            <li><router-link to="/filmy?genre=Ужасы">Ужасы</router-link></li>
          </ul>
        </div>
      </li>
      
      <li>
        <a href="#" @click.prevent>Сериалы</a>
        <div class="nav-bar___nav-hidden anim">
          <ul class="nav-bar___nav-hidden-col">
            <li><router-link to="/serialy">Все</router-link></li>
            <li>По году:</li>
            <li><router-link to="/serialy?year=2025">2025</router-link></li>
            <li><router-link to="/serialy?year=2024">2024</router-link></li>
            <li><router-link to="/serialy?year=2023">2023</router-link></li>
          </ul>
          <ul class="nav-bar___nav-hidden-col">
            <li>По жанрам:</li>
            <li><router-link to="/serialy?special=turkish">Турецкие сериалы</router-link></li>
            <li><router-link to="/serialy?special=doramas">Дорамы</router-link></li>
            <li><router-link to="/serialy?genre=Биография">Биография</router-link></li>
            <li><router-link to="/serialy?genre=Вестерн">Вестерн</router-link></li>
            <li><router-link to="/serialy?genre=Военный">Военный</router-link></li>
            <li><router-link to="/serialy?genre=Боевик">Боевик</router-link></li>
            <li><router-link to="/serialy?genre=Документальный">Документальные</router-link></li>
            <li><router-link to="/serialy?genre=Драма">Драмы</router-link></li>
            <li><router-link to="/serialy?genre=Детектив">Детективные</router-link></li>
            <li><router-link to="/serialy?genre=Семейный">Детские</router-link></li>
          </ul>
          <ul class="nav-bar___nav-hidden-col">
            <li><router-link to="/serialy?genre=Комедия">Комедии</router-link></li>
            <li><router-link to="/serialy?genre=История">Исторические</router-link></li>
            <li><router-link to="/serialy?genre=Криминал">Криминал</router-link></li>
            <li><router-link to="/serialy?genre=Мелодрама">Мелодрамы</router-link></li>
            <li><router-link to="/serialy?genre=Спорт">Спорт</router-link></li>
            <li><router-link to="/serialy?genre=Триллер">Триллеры</router-link></li>
            <li><router-link to="/serialy?genre=Мюзиклы">Мюзиклы</router-link></li>
            <li><router-link to="/serialy?genre=Приключения">Приключения</router-link></li>
            <li><router-link to="/serialy?genre=Ужасы">Ужасы</router-link></li>
            <li><router-link to="/serialy?genre=Фантастика">Фантастика</router-link></li>
            <li><router-link to="/serialy?genre=Фэнтези">Фэнтези</router-link></li>
            <li><router-link to="/serialy?genre=Семейный">Семейные</router-link></li>
          </ul>
        </div>
      </li>
      
      <li><router-link to="/multfilmy">Мультфильмы</router-link></li>
      <li><router-link to="/anime">Аниме</router-link></li>
      <li><router-link to="/novinki">Новинки</router-link></li>
      <li><router-link to="/top-all-time">Топ</router-link></li>
    </ul>
    
    <div class="header__search search-panel flex-1 js-this-in-mobile-menu" ref="searchContainer">
      <form @submit.prevent="performSearch" class="js-search-form" novalidate="novalidate">
        <input 
          v-model="searchInput"
          class="srchpanel__input input-bigger" 
          placeholder="Поиск по сайту..." 
          type="text" 
          autocomplete="off"
          @keydown.enter.prevent="performSearch"
        >
        <button 
          class="srchpanel__btn btn-nobg btn-square fal fa-search" 
          aria-label="Искать" 
          type="submit"
        ></button>
      </form>
      <div v-if="showSuggestions && suggestions.length" class="search-suggestions">
        <ul>
          <li v-for="suggestion in suggestions" :key="suggestion.id" @click="selectSuggestion(suggestion)">
            <img :src="getPosterUrl(suggestion.poster)" :alt="suggestion.title" class="suggestion-poster" loading="lazy" decoding="async" width="50" height="75">
            <div class="suggestion-info">
              <div class="suggestion-title">{{ suggestion.title }} ({{ suggestion.year }})</div>
              <div class="suggestion-genres">{{ suggestion.genres.join(', ') }}</div>
              <div class="suggestion-ratings">
                <span v-if="suggestion.kpRating" class="rating-kp">KP: {{ suggestion.kpRating }}</span>
                <span v-if="suggestion.imdbRating" class="rating-imdb">IMDb: {{ formatRating(suggestion.imdbRating) }}</span>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>
    
    <button 
      class="header__btn-menu btn-square fal fa-bars fa-1.3x d-none js-show-mobile-menu" 
      aria-label="Открыть моб меню"
      @click="openMobileMenu"
    ></button>
    
    <button 
      @click="toggleTheme"
      class="nav-bar___theme-toggle btn-nobg btn-square fal fa-sun fa-2x js-theme-toggle" 
      aria-label="Сменить цвет сайта"
    ></button>
  </header>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const emit = defineEmits(['search', 'open-mobile-menu'])

const searchInput = ref('')
const suggestions = ref([])
const showSuggestions = ref(false)
const searchContainer = ref(null)

let debounceTimer

function formatRating(val) {
  const n = parseFloat(String(val).replace(',', '.'))
  if (!isFinite(n)) return String(val ?? '')
  const rounded = Math.round(n * 10) / 10
  return Math.abs(rounded - Math.round(rounded)) < 1e-9
    ? String(Math.round(rounded))
    : rounded.toFixed(1)
}

const getPosterUrl = (posterPath) => {
  if (!posterPath) return '/assets/ProsmotrZone_site/images/bg.jpg'
  if (posterPath.startsWith('http')) return posterPath
  return posterPath.startsWith('/') ? posterPath : `/${posterPath}`
};

watch(searchInput, (newValue) => {
  clearTimeout(debounceTimer)
  if (newValue.length === 0) {
    suggestions.value = []
    showSuggestions.value = false
    return
  }
  debounceTimer = setTimeout(async () => {
    if (newValue.length > 0) {
      try {
        const response = await fetch(`/api/search-suggestions?q=${encodeURIComponent(newValue)}`)
        if (response.ok) {
          const data = await response.json()
          suggestions.value = data
          showSuggestions.value = true
        } else {
          console.error('Ошибка при получении подсказок')
          suggestions.value = []
        }
      } catch (error) {
        console.error('Ошибка сети:', error)
        suggestions.value = []
      }
    } else {
      suggestions.value = []
    }
  }, 300)
})

// Скрывать подсказки при смене маршрута (в т.ч. после поиска)
watch(() => router.currentRoute.value.fullPath, () => {
  showSuggestions.value = false
  suggestions.value = []
})

const selectSuggestion = (suggestion) => {
  searchInput.value = ''
  suggestions.value = []
  showSuggestions.value = false
  router.push(`/${suggestion.category}/${suggestion.id}`)
}

const handleClickOutside = (event) => {
  if (searchContainer.value && !searchContainer.value.contains(event.target)) {
    showSuggestions.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const performSearch = () => {
  const q = searchInput.value.trim()
  if (!q) return
  showSuggestions.value = false
  suggestions.value = []
  const inputEl = searchContainer.value?.querySelector('input')
  if (inputEl) inputEl.blur()
  emit('search', q)
}

const openMobileMenu = () => {
  emit('open-mobile-menu')
}

const toggleTheme = () => {
  const bd = document.body
  let ls = JSON.parse(localStorage.getItem('settlf'))
  
  if (!ls || ls[0] === 'lt') {
    // Переключить на темную тему
    localStorage.setItem('settlf', JSON.stringify(['dt', 'btn1']))
    bd.className = ''
    bd.classList.add('dt', 'btn1', 'branding-enabled')
    bd.setAttribute('data-theme', 'dark')
  } else {
    // Переключить на светлую тему
    localStorage.setItem('settlf', JSON.stringify(['lt', 'btn1']))
    bd.className = ''
    bd.classList.add('lt', 'btn1', 'branding-enabled')
    bd.removeAttribute('data-theme')
  }
}
</script>

<style scoped>
.search-panel {
  position: relative;
}

.search-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background-color: #fff;
  border: 1px solid #e0e0e0;
  border-top: none;
  z-index: 1000;
  max-height: 500px;
  overflow-y: auto;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  border-radius: 0 0 4px 4px;
}

.search-suggestions ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.search-suggestions li {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid #e0e0e0;
}

.search-suggestions li:last-child {
  border-bottom: none;
}

.search-suggestions li:hover {
  background-color: #f5f5f5;
}

.suggestion-poster {
  width: 50px;
  height: 75px;
  object-fit: cover;
  margin-right: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}

.suggestion-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow: hidden;
}

.suggestion-title {
  font-weight: 600;
  font-size: 1em;
  color: #222;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.suggestion-year {
  font-size: 0.9em;
  color: #888;
}

.suggestion-genres {
  font-size: 0.85em;
  color: #555;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.suggestion-ratings {
  display: flex;
  gap: 10px;
  font-size: 0.85em;
  font-weight: bold;
}

.rating-kp {
  color: #ff9900;
}

.rating-imdb {
  color: #f5c518;
}

/* Dark theme styles */
.dt .search-suggestions {
    background-color: #252525;
    border-color: #383838;
}

.dt .search-suggestions li {
    border-bottom-color: #383838;
}

.dt .search-suggestions li:hover {
    background-color: #333;
}

.dt .suggestion-title {
  color: #f5f5f5;
}

.dt .suggestion-genres {
  color: #aaa;
}

.dt .suggestion-year {
  color: #aaa;
}
</style>