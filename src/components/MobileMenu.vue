<template>
  <!-- Overlay -->
  <div 
    v-if="isVisible" 
    class="overlay"
    @click="closeMobileMenu"
  ></div>
  
  <!-- Mobile Menu -->
  <div 
    class="mobile-menu"
    :class="{ 'is-active mobile-menu--is-generated': isVisible }"
  >
    <div class="mobile-menu__header d-flex ai-center">
      <router-link to="/" class="navbar__logo logo mr-auto">
        Lord<span>Film</span>
      </router-link>
      <button 
        class="mobile-menu__btn-close btn-nobg btn-square fal fa-times" 
        aria-label="Закрыть мобильное меню"
        @click="closeMobileMenu"
      ></button>
    </div>
    
    <div class="mobile-menu__content">
      <!-- Навигация -->
      <ul class="navbar__nav d-flex c-gap-20">
        <li>
          <a href="#" @click.prevent>Фильмы</a>
          <div class="navbar__nav-hidden anim">
            <ul class="navbar__nav-hidden-col">
              <li><router-link to="/filmy" @click="closeMobileMenu">Все</router-link></li>
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
              <li><a href="#" @click.prevent="navigate('/filmy?genre=Военные')">Военные</a></li>
              <li><a href="#" @click.prevent="navigate('/filmy?genre=Документальный')">Документальные</a></li>
              <li><a href="#" @click.prevent="navigate('/filmy?genre=Детектив')">Детективы</a></li>
              <li><a href="#" @click.prevent="navigate('/filmy?genre=Семейный')">Детские</a></li>
              <li><a href="#" @click.prevent="navigate('/filmy?genre=Драмы')">Драмы</a></li>
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
              <li><router-link to="/serialy" @click="closeMobileMenu">Все</router-link></li>
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
              <li><a href="#" @click.prevent="navigate('/serialy?genre=Документальный')">Документальный</a></li>
              <li><a href="#" @click.prevent="navigate('/serialy?genre=Детектив')">Детектив</a></li>
              <li><a href="#" @click.prevent="navigate('/serialy?genre=Семейный')">Детский</a></li>
              <li><a href="#" @click.prevent="navigate('/serialy?genre=Драма')">Драма</a></li>
            </ul>
            <ul class="navbar__nav-hidden-col">
              <li><a href="#" @click.prevent="navigate('/serialy?genre=История')">Исторический</a></li>
              <li><a href="#" @click.prevent="navigate('/serialy?genre=Комедия')">Комедия</a></li>
              <li><a href="#" @click.prevent="navigate('/serialy?genre=Криминал')">Криминал</a></li>
              <li><a href="#" @click.prevent="navigate('/serialy?genre=Мелодрама')">Мелодрама</a></li>
              <li><a href="#" @click.prevent="navigate('/serialy?genre=Музыка')">Музыка</a></li>
              <li><a href="#" @click.prevent="navigate('/serialy?genre=Приключения')">Приключения</a></li>
              <li><a href="#" @click.prevent="navigate('/serialy?genre=Семейный')">Семейный</a></li>
              <li><a href="#" @click.prevent="navigate('/serialy?genre=Спорт')">Спорт</a></li>
              <li><a href="#" @click.prevent="navigate('/serialy?genre=Триллер')">Триллер</a></li>
              <li><a href="#" @click.prevent="navigate('/serialy?genre=Ужасы')">Ужасы</a></li>
              <li><a href="#" @click.prevent="navigate('/serialy?genre=Фантастика')">Фантастика</a></li>
              <li><a href="#" @click.prevent="navigate('/serialy?genre=Фэнтези')">Фэнтези</a></li>
            </ul>
          </div>
        </li>
        <li><router-link to="/multfilmy" @click="closeMobileMenu">Мультфильмы</router-link></li>
        <li><router-link to="/anime" @click="closeMobileMenu">Аниме</router-link></li>
        <li><router-link to="/top100" @click="closeMobileMenu">ТОП-100</router-link></li>
      </ul>
      
      <!-- Поиск -->
      <div class="header__search search-panel flex-1">
        <form class="js-search-form" method="post" @submit.prevent="handleSearch">
          <input type="hidden" name="do" value="search">
          <input type="hidden" name="subaction" value="search">
          <input 
            class="search-panel__input input-bigger" 
            name="story" 
            placeholder="Поиск по сайту..." 
            type="text" 
            autocomplete="off"
            v-model="searchQuery"
          >
          <button class="search-panel__btn btn-nobg btn-square fal fa-search" aria-label="Искать" type="submit"></button>
        </form>
        
        <!-- Результаты поиска для мобильного меню -->
        <div v-if="paginatedResults.length > 0">
          <div 
            class="grid-items count-items search-results-block"
            style="display: grid; padding: 0px; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 20px;"
          >
            <MovieCard 
              v-for="movie in paginatedResults" 
              :key="movie.id" 
              :movie="movie"
            />
          </div>

          <div v-if="hasMore" class="pagination ignore-select d-flex jc-center" style="margin-top: 16px;">
            <div class="page-nav__btn-loader d-flex jc-center ai-center w-100">
              <a href="#" @click.prevent="loadMore">
                <span class="fal fa-redo js-search-load-more"></span>Загрузить еще
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import MovieCard from './MovieCard.vue'
import moviesData from '../../movies-data.json'

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const searchQuery = ref('')
const searchResults = ref([])
const visibleResultsCount = ref(24)

const paginatedResults = computed(() => {
  return searchResults.value.slice(0, visibleResultsCount.value)
})

const hasMore = computed(() => {
  return searchResults.value.length > visibleResultsCount.value
})

// Поиск в мобильном меню
const handleSearch = () => {
  if (searchQuery.value.trim()) {
    visibleResultsCount.value = 24
    const q = searchQuery.value.toLowerCase().trim()
    searchResults.value = moviesData.movies.filter(movie => {
      if (movie.id === 'index') return false
      const fields = [
        movie.title,
        movie.originalTitle,
        movie.altTitle,
        movie.alt_title,
        movie.description,
        movie.actors
      ]
      return fields.some(val => {
        if (Array.isArray(val)) {
          return val.join(' ').toLowerCase().includes(q)
        }
        return (val ? String(val) : '').toLowerCase().includes(q)
      })
    })
  } else {
    searchResults.value = []
  }
}

const loadMore = () => {
  visibleResultsCount.value += 24
}

// Закрытие мобильного меню
const closeMobileMenu = () => {
  emit('close')
}

// Навигация как в header (router.push + reload)
const router = useRouter()
const navigate = (path) => {
  emit('close')
  router.push(path).then(() => {
    window.location.reload()
  })
}

// Очистка поиска при закрытии меню
watch(() => props.isVisible, (newVal) => {
  if (!newVal) {
    searchQuery.value = ''
    searchResults.value = []
    visibleResultsCount.value = 24
  }
})

// Управление классом body
watch(() => props.isVisible, (newVal) => {
  if (newVal) {
    document.body.classList.add('mobile-menu-is-opened')
  } else {
    document.body.classList.remove('mobile-menu-is-opened')
  }
})
</script>