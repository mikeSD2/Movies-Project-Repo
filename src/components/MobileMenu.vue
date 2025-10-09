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
      <!-- Поиск -->
      <div class="header__search search-panel flex-1" style="margin-bottom: 20px;">
        <form class="js-search-form" method="post" @submit.prevent="performSearch">
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
      </div>
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
              <li><router-link to="/filmy?genre=Биография" @click="closeMobileMenu">Биографические</router-link></li>
              <li><router-link to="/filmy?genre=Боевик" @click="closeMobileMenu">Боевики</router-link></li>
              <li><router-link to="/filmy?genre=Вестерн" @click="closeMobileMenu">Вестерны</router-link></li>
              <li><router-link to="/filmy?genre=Военный" @click="closeMobileMenu">Военные</router-link></li>
              <li><router-link to="/filmy?genre=Документальный" @click="closeMobileMenu">Документальные</router-link></li>
              <li><router-link to="/filmy?genre=Детектив" @click="closeMobileMenu">Детективы</router-link></li>
              <li><router-link to="/filmy?genre=Семейный" @click="closeMobileMenu">Детские</router-link></li>
              <li><router-link to="/filmy?genre=Драмы" @click="closeMobileMenu">Драмы</router-link></li>
              <li><router-link to="/filmy?genre=История" @click="closeMobileMenu">Исторические</router-link></li>
              <li><router-link to="/filmy?genre=Комедия" @click="closeMobileMenu">Комедии</router-link></li>
            </ul>
            <ul class="navbar__nav-hidden-col">
              <li><router-link to="/filmy?genre=Криминал" @click="closeMobileMenu">Криминал</router-link></li>
              <li><router-link to="/filmy?genre=Мелодрама" @click="closeMobileMenu">Мелодрамы</router-link></li>
              <li><router-link to="/filmy?genre=Приключения" @click="closeMobileMenu">Приключения</router-link></li>
              <li><router-link to="/filmy?genre=Семейный" @click="closeMobileMenu">Семейные</router-link></li>
              <li><router-link to="/filmy?genre=Спорт" @click="closeMobileMenu">Спорт</router-link></li>
              <li><router-link to="/filmy?genre=Триллер" @click="closeMobileMenu">Триллеры</router-link></li>
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
              <li><router-link to="/serialy?special=doramas" @click="closeMobileMenu">Дорамы</router-link></li>
              <li><router-link to="/serialy?special=turkish" @click="closeMobileMenu">Турецкие сериалы</router-link></li>
              <li><router-link to="/serialy?genre=Биография" @click="closeMobileMenu">Биография</router-link></li>
              <li><router-link to="/serialy?genre=Боевик" @click="closeMobileMenu">Боевик</router-link></li>
              <li><router-link to="/serialy?genre=Вестерн" @click="closeMobileMenu">Вестерн</router-link></li>
              <li><router-link to="/serialy?genre=Военный" @click="closeMobileMenu">Военный</router-link></li>
              <li><router-link to="/serialy?genre=Документальный" @click="closeMobileMenu">Документальный</router-link></li>
              <li><router-link to="/serialy?genre=Детектив" @click="closeMobileMenu">Детектив</router-link></li>
              <li><router-link to="/serialy?genre=Детский" @click="closeMobileMenu">Детский</router-link></li>
              <li><router-link to="/serialy?genre=Драма" @click="closeMobileMenu">Драма</router-link></li>
            </ul>
            <ul class="navbar__nav-hidden-col">
              <li><router-link to="/serialy?genre=История" @click="closeMobileMenu">Исторический</router-link></li>
              <li><router-link to="/serialy?genre=Комедия" @click="closeMobileMenu">Комедия</router-link></li>
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
        <li><router-link to="/tops" @click="closeMobileMenu">ТОПЫ</router-link></li>
      </ul>
      
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'search'])

const searchQuery = ref('')

const performSearch = () => {
  if (searchQuery.value.trim()) {
    emit('search', searchQuery.value)
    closeMobileMenu()
  }
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