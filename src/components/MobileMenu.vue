<template>
  <!-- Оверлей -->
  <div 
    v-if="isVisible" 
    class="overlay"
    @click="closeMobileMenu"
  ></div>
  
  <!-- Mobile -->
  <div 
    class="mobile-menu"
    :class="{ 'is-active mobile-menu--is-generated': isVisible }"
  >
    <div class="mobile-menu___header d-flex ai-center">
      <router-link to="/" class="navigation_panel__logo logo mr-auto">
        LordFilms
      </router-link>
      <button 
        class="mobile-menu___btn-close btn-nobg btn-square fal fa-times" 
        aria-label="Закрыть мобильное меню"
        @click="closeMobileMenu"
      ></button>
    </div>
    
    <div class="mobile-menu___content">
      <!-- Search -->
      <div class="header__search search-panel flex-1" style="margin-bottom: 20px;">
        <form class="js-search-form" method="post" @submit.prevent="performSearch">
          <input type="hidden" name="do" value="search">
          <input type="hidden" name="subaction" value="search">
          <input 
            class="my_searchpanel_input input-bigger" 
            name="story" 
            placeholder="Поиск по сайту..." 
            type="text" 
            autocomplete="off"
            v-model="searchQuery"
          >
          <button class="my_searchpanel_btn btn-nobg btn-square fal fa-search" aria-label="Искать" type="submit"></button>
        </form>
      </div>
      <!-- Nav -->
      <ul class="navigation_panel__nav d-flex c-gap-20" @click.capture="onNavClick">
      <li>
        <a href="#" @click.prevent>Фильмы</a>
        <div class="navigation_panel__nav-hidden anim">
            <ul class="navigation_panel__nav-hidden-col">
              <li><router-link to="/filmy">Все</router-link></li>
              <li>По году:</li>
              <li><router-link to="/filmy?year=2025">2025</router-link></li>
              <li><router-link to="/filmy?year=2024">2024</router-link></li>
              <li><router-link to="/filmy?year=2023">2023</router-link></li>
            </ul>
            <ul class="navigation_panel__nav-hidden-col">
              <li>По жанрам:</li>
              <li><router-link to="/filmy?genre=Боевик">Боевики</router-link></li>
              <li><router-link to="/filmy?genre=Драма">Драмы</router-link></li>
              <li><router-link to="/filmy?genre=История">Исторические</router-link></li>
              <li><router-link to="/filmy?genre=Вестерн">Вестерны</router-link></li>
              <li><router-link to="/filmy?genre=Биография">Биографические</router-link></li>
              <li><router-link to="/filmy?genre=Военный">Военные</router-link></li>
              <li><router-link to="/filmy?genre=Детектив">Детективы</router-link></li>
              <li><router-link to="/filmy?genre=Криминал">Криминал</router-link></li>
              <li><router-link to="/filmy?genre=Семейный">Детские</router-link></li>
              <li><router-link to="/filmy?genre=Комедия">Комедии</router-link></li>
            </ul>
            <ul class="navigation_panel__nav-hidden-col">
            <li><router-link to="/filmy?genre=Документальный">Документальные</router-link></li>
            <li><router-link to="/filmy?genre=Мелодрама">Мелодрамы</router-link></li>
            <li><router-link to="/filmy?genre=Приключения">Приключения</router-link></li>
            <li><router-link to="/filmy?genre=Семейный">Семейные</router-link></li>
            <li><router-link to="/filmy?genre=Фэнтези">Фэнтези</router-link></li>
            <li><router-link to="/filmy?genre=Спорт">Спорт</router-link></li>
            <li><router-link to="/filmy?genre=Триллер">Триллеры</router-link></li>
            <li><router-link to="/filmy?genre=Ужасы">Ужасы</router-link></li>
            <li><router-link to="/filmy?genre=Фантастика">Фантастика</router-link></li>
            </ul>
          </div>
        </li>
        <li>
          <a href="#" @click.prevent>Сериалы</a>
          <div class="navigation_panel__nav-hidden anim">
            <ul class="navigation_panel__nav-hidden-col">
              <li><router-link to="/serialy">Все</router-link></li>
              <li>По году:</li>
              <li><router-link to="/serialy?year=2025">2025</router-link></li>
              <li><router-link to="/serialy?year=2024">2024</router-link></li>
              <li><router-link to="/serialy?year=2023">2023</router-link></li>
            </ul>
            <ul class="navigation_panel__nav-hidden-col">
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
            <ul class="navigation_panel__nav-hidden-col">
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
        <li><router-link to="/top-100">Топ-100</router-link></li>
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

// Делегированный клик по ссылкам: закрываем меню на навигации
const onNavClick = (e) => {
  const a = e.target.closest('a')
  if (!a) return
  const href = a.getAttribute('href')
  if (href && href !== '#') closeMobileMenu()
}
</script>