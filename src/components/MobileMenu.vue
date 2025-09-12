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
              <li><router-link to="/filmy?year=2025" @click="closeMobileMenu">2025</router-link></li>
              <li><router-link to="/filmy?year=2024" @click="closeMobileMenu">2024</router-link></li>
              <li><router-link to="/filmy?year=2023" @click="closeMobileMenu">2023</router-link></li>
            </ul>
            <ul class="navbar__nav-hidden-col">
              <li>По жанрам:</li>
              <li><router-link to="/filmy?genre=Биографические" @click="closeMobileMenu">Биографические</router-link></li>
              <li><router-link to="/filmy?genre=Боевики" @click="closeMobileMenu">Боевики</router-link></li>
              <li><router-link to="/filmy?genre=Вестерны" @click="closeMobileMenu">Вестерны</router-link></li>
              <li><router-link to="/filmy?genre=Военные" @click="closeMobileMenu">Военные</router-link></li>
              <li><router-link to="/filmy?genre=Документальные" @click="closeMobileMenu">Документальные</router-link></li>
              <li><router-link to="/filmy?genre=Детективы" @click="closeMobileMenu">Детективы</router-link></li>
              <li><router-link to="/filmy?genre=Детские" @click="closeMobileMenu">Детские</router-link></li>
              <li><router-link to="/filmy?genre=Драмы" @click="closeMobileMenu">Драмы</router-link></li>
              <li><router-link to="/filmy?genre=Исторические" @click="closeMobileMenu">Исторические</router-link></li>
              <li><router-link to="/filmy?genre=Комедии" @click="closeMobileMenu">Комедии</router-link></li>
            </ul>
            <ul class="navbar__nav-hidden-col">
              <li><router-link to="/filmy?genre=Криминал" @click="closeMobileMenu">Криминал</router-link></li>
              <li><router-link to="/filmy?genre=Мелодрамы" @click="closeMobileMenu">Мелодрамы</router-link></li>
              <li><router-link to="/filmy?genre=Приключения" @click="closeMobileMenu">Приключения</router-link></li>
              <li><router-link to="/filmy?genre=Семейные" @click="closeMobileMenu">Семейные</router-link></li>
              <li><router-link to="/filmy?genre=Спорт" @click="closeMobileMenu">Спорт</router-link></li>
              <li><router-link to="/filmy?genre=Триллеры" @click="closeMobileMenu">Триллеры</router-link></li>
              <li><router-link to="/filmy?genre=Ужасы" @click="closeMobileMenu">Ужасы</router-link></li>
              <li><router-link to="/filmy?genre=Фантастика" @click="closeMobileMenu">Фантастика</router-link></li>
              <li><router-link to="/filmy?genre=Фэнтези" @click="closeMobileMenu">Фэнтези</router-link></li>
            </ul>
          </div>
        </li>
        <li>
          <a href="#" @click.prevent>Сериалы</a>
          <div class="navbar__nav-hidden anim">
            <ul class="navbar__nav-hidden-col">
              <li><router-link to="/serialy" @click="closeMobileMenu">Все</router-link></li>
              <li>По году:</li>
              <li><router-link to="/serialy?year=2023" @click="closeMobileMenu">2023</router-link></li>
              <li><router-link to="/serialy?year=2024" @click="closeMobileMenu">2024</router-link></li>
              <li><router-link to="/serialy?year=2025" @click="closeMobileMenu">2025</router-link></li>
            </ul>
            <ul class="navbar__nav-hidden-col">
              <li>По жанрам:</li>
              <li><router-link to="/serialy?genre=Биография" @click="closeMobileMenu">Биография</router-link></li>
              <li><router-link to="/serialy?genre=Боевик" @click="closeMobileMenu">Боевик</router-link></li>
              <li><router-link to="/serialy?genre=Вестерн" @click="closeMobileMenu">Вестерн</router-link></li>
              <li><router-link to="/serialy?genre=Военный" @click="closeMobileMenu">Военный</router-link></li>
              <li><router-link to="/serialy?genre=Документальный" @click="closeMobileMenu">Документальный</router-link></li>
              <li><router-link to="/serialy?genre=Детектив" @click="closeMobileMenu">Детектив</router-link></li>
              <li><router-link to="/serialy?genre=Детский" @click="closeMobileMenu">Детский</router-link></li>
              <li><router-link to="/serialy?genre=Драма" @click="closeMobileMenu">Драма</router-link></li>
              <li><router-link to="/serialy?genre=Исторический" @click="closeMobileMenu">Исторический</router-link></li>
              <li><router-link to="/serialy?genre=Комедия" @click="closeMobileMenu">Комедия</router-link></li>
            </ul>
            <ul class="navbar__nav-hidden-col">
              <li><router-link to="/serialy?genre=Криминал" @click="closeMobileMenu">Криминал</router-link></li>
              <li><router-link to="/serialy?genre=Мелодрама" @click="closeMobileMenu">Мелодрама</router-link></li>
              <li><router-link to="/serialy?genre=Музыка" @click="closeMobileMenu">Музыка</router-link></li>
              <li><router-link to="/serialy?genre=Приключения" @click="closeMobileMenu">Приключения</router-link></li>
              <li><router-link to="/serialy?genre=Семейный" @click="closeMobileMenu">Семейный</router-link></li>
              <li><router-link to="/serialy?genre=Спорт" @click="closeMobileMenu">Спорт</router-link></li>
              <li><router-link to="/serialy?genre=Триллер" @click="closeMobileMenu">Триллер</router-link></li>
              <li><router-link to="/serialy?genre=Ужасы" @click="closeMobileMenu">Ужасы</router-link></li>
              <li><router-link to="/serialy?genre=Фантастика" @click="closeMobileMenu">Фантастика</router-link></li>
              <li><router-link to="/serialy?genre=Фэнтези" @click="closeMobileMenu">Фэнтези</router-link></li>
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
