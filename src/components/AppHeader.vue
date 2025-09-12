<template>
  <header class="header d-flex ai-center r-gap-10 c-gap-10 anim" id="header">
    <router-link to="/" class="navbar__logo logo">
      Lord<span>Film</span>
    </router-link>
    
    <ul class="navbar__nav d-flex c-gap-20 js-this-in-mobile-menu">
      <li>
        <a href="#" @click.prevent>Фильмы</a>
        <div class="navbar__nav-hidden anim">
          <ul class="navbar__nav-hidden-col">
            <li><router-link to="/filmy">Все</router-link></li>
            <li>По году:</li>
            <li><a href="#" @click.prevent="navigate('/filmy?year=2025')">2025</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?year=2024')">2024</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?year=2023')">2023</a></li>
          </ul>
          <ul class="navbar__nav-hidden-col">
            <li>По жанрам:</li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Биография')">Биографические</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Боевик')">Боевики</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Вестерн')">Вестерны</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Военный')">Военные</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Документальный')">Документальные</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Детектив')">Детективы</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Семейный')">Детские</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Драма')">Драмы</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=История')">Исторические</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Комедия')">Комедии</a></li>
          </ul>
          <ul class="navbar__nav-hidden-col">
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Криминал')">Криминал</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Мелодрама')">Мелодрамы</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Приключения')">Приключения</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Семейный')">Семейные</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Спорт')">Спорт</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Триллер')">Триллеры</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Ужасы')">Ужасы</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Фантастика')">Фантастика</a></li>
            <li><a href="#" @click.prevent="navigate('/filmy?genre=Фэнтези')">Фэнтези</a></li>
          </ul>
        </div>
      </li>
      
      <li>
        <a href="#" @click.prevent>Сериалы</a>
        <div class="navbar__nav-hidden anim">
          <ul class="navbar__nav-hidden-col">
            <li><router-link to="/serialy">Все</router-link></li>
            <li>По году:</li>
            <li><a href="#" @click.prevent="navigate('/serialy?year=2023')">2023</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?year=2024')">2024</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?year=2025')">2025</a></li>
          </ul>
          <ul class="navbar__nav-hidden-col">
            <li>По жанрам:</li>
            <li><a href="#" @click.prevent="navigate('/serialy?special=doramas')">Дорамы</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?special=turkish')">Турецкие сериалы</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Биография')">Биография</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Боевик')">Боевик</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Вестерн')">Вестерн</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Военный')">Военный</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Документальный')">Документальные</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Детектив')">Детективные</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Семейный')">Детские</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Драма')">Драмы</a></li>
          </ul>
          <ul class="navbar__nav-hidden-col">
            <li><a href="#" @click.prevent="navigate('/serialy?genre=История')">Исторические</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Комедия')">Комедии</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Криминал')">Криминал</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Мелодрама')">Мелодрамы</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Музыка')">Музыка</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Приключения')">Приключения</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Семейный')">Семейные</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Спорт')">Спорт</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Триллер')">Триллеры</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Ужасы')">Ужасы</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Фантастика')">Фантастика</a></li>
            <li><a href="#" @click.prevent="navigate('/serialy?genre=Фэнтези')">Фэнтези</a></li>
          </ul>
        </div>
      </li>
      
      <li><router-link to="/multfilmy">Мультфильмы</router-link></li>
      <li><router-link to="/anime">Аниме</router-link></li>
      <li><router-link to="/top100">ТОПЫ</router-link></li>
    </ul>
    
    <div class="header__search search-panel flex-1 js-this-in-mobile-menu" ref="searchContainer">
      <form @submit.prevent="performSearch" class="js-search-form" novalidate="novalidate">
        <input 
          v-model="searchInput"
          class="search-panel__input input-bigger" 
          placeholder="Поиск по сайту..." 
          type="text" 
          autocomplete="off"
          @keydown.enter.prevent="performSearch"
        >
        <button 
          class="search-panel__btn btn-nobg btn-square fal fa-search" 
          aria-label="Искать" 
          type="submit"
        ></button>
      </form>
      <div v-if="showSuggestions && suggestions.length" class="search-suggestions">
        <ul>
          <li v-for="suggestion in suggestions" :key="suggestion.id" @click="selectSuggestion(suggestion)">
            <img :src="getPosterUrl(suggestion.poster)" :alt="suggestion.title" class="suggestion-poster">
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
      class="navbar__theme-toggle btn-nobg btn-square fal fa-sun fa-2x js-theme-toggle" 
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
  if (!posterPath) return '/assets/lordfilm-website/images/no-poster.jpg'
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

const navigate = (path) => {
  router.push(path).then(() => {
    window.location.reload()
  })
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