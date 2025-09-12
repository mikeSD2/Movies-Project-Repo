<template>
  <section class="sect">
    <div class="section__header d-flex ai-center r-gap-20 c-gap-20">
      <h1 class="section__title flex-1">{{ categoryTitle }}</h1>
      
      <!-- Фильтры -->
      <div class="filters d-flex c-gap-10">
        <select v-model="selectedYear" @change="applyFilters" class="filter-select">
          <option value="">Все годы</option>
          <option v-for="year in availableYears" :key="year" :value="year">
            {{ year }}
          </option>
        </select>
        
        <select v-model="selectedGenre" @change="applyFilters" class="filter-select">
          <option value="">Все жанры</option>
          <option v-for="genre in availableGenres" :key="genre" :value="genre">
            {{ genre }}
          </option>
        </select>
        
        <select v-model="sortBy" @change="applyFilters" class="filter-select">
          <option value="year">По году</option>
          <option value="rating">По рейтингу</option>
          <option value="title">По названию</option>
        </select>
      </div>
    </div>
    
    <div class="section__content grid-items" id="grid-items">
      <MovieCard 
        v-for="movie in paginatedMovies" 
        :key="movie.id" 
        :movie="movie" 
      />
    </div>
    
    <!-- Пагинация -->
    <div class="pagination ignore-select d-flex jc-center" id="pagination">
      <!-- Кнопка "Загрузить еще" -->
      <div v-if="hasMoreItems" class="page-nav__btn-loader d-flex jc-center ai-center w-100">
        <a href="#" @click.prevent="loadMore">
          <span class="fal fa-redo"></span>Загрузить еще
        </a>
      </div>

      <!-- Классическая пагинация -->
      <div v-if="totalPages > 1" class="page-nav__pages d-flex jc-center">
        <span v-if="currentPage > 1">
          <i @click="goToPage(currentPage - 1)" class="page-nav__btn page-nav__btn--prev fal fa-arrow-left"></i>
        </span>
        
        <div class="page-nav__pages d-flex jc-center">
          <span v-for="page in visiblePages" :key="page">
            <span v-if="page === '...'" class="nav_ext">{{ page }}</span>
            <span v-else-if="page === currentPage">{{ page }}</span>
            <a v-else href="#" @click.prevent="goToPage(page)">{{ page }}</a>
          </span>
        </div>
        
        <span v-if="currentPage < totalPages">
          <i @click="goToPage(currentPage + 1)" class="page-nav__btn page-nav__btn--next fal fa-arrow-right"></i>
        </span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import MovieCard from './MovieCard.vue'
import moviesData from '../../movies-data.json'

const props = defineProps({
  category: String
})

const route = useRoute()

// Реактивные данные
const currentPage = ref(1)
const itemsPerPage = ref(24)
const pagesLoaded = ref(1)
const selectedYear = ref('')
const selectedGenre = ref('')
const selectedCountry = ref('')
const selectedTranslation = ref('')
const sortBy = ref('year')

// Спец-фильтр из меню: doramas/turkish
const specialFilter = ref('')

// Заголовок категории
const categoryTitle = computed(() => {
  return moviesData.categories[props.category] || 'Контент'
})

// Все фильмы текущей категории (исключаем placeholder 'index')
const categoryMovies = computed(() => {
  return moviesData.movies.filter(movie => movie.category === props.category && movie.id !== 'index')
})

// Доступные года
const availableYears = computed(() => {
  const years = [...new Set(categoryMovies.value.map(movie => movie.year))]
  return years.sort((a, b) => b - a)
})

// Доступные жанры
const availableGenres = computed(() => {
  const genres = new Set()
  categoryMovies.value.forEach(movie => {
    if (movie.genres) {
      movie.genres.forEach(genre => genres.add(genre))
    }
  })
  return Array.from(genres).sort()
})

// Отфильтрованные фильмы
const filteredMovies = computed(() => {
  let filtered = [...categoryMovies.value]

  // Спец-фильтры
  if (specialFilter.value) {
    const asianKeywords = [
      'южная корея','корея','северная корея',
      'япония','китай','тайвань','гонконг',
      'таиланд','индонезия','малайзия','вьетнам',
      'сингапур','филиппины'
    ]
    const isAsian = (countryStr) => {
      if (!countryStr) return false
      const s = String(countryStr).toLowerCase()
      return asianKeywords.some(k => s.includes(k))
    }
    if (specialFilter.value === 'doramas') {
      filtered = filtered.filter(movie => isAsian(movie.country))
    } else if (specialFilter.value === 'turkish') {
      filtered = filtered.filter(movie => /турция/i.test(movie.country || ''))
    }
  }
  
  // Фильтр по году
  if (selectedYear.value) {
    filtered = filtered.filter(movie => movie.year == selectedYear.value)
  }
  
  // Фильтр по жанру
  if (selectedGenre.value) {
    filtered = filtered.filter(movie => 
      movie.genres && movie.genres.includes(selectedGenre.value)
    )
  }
  
  // Фильтр по стране
  if (selectedCountry.value) {
    filtered = filtered.filter(movie => 
      movie.country && movie.country.includes(selectedCountry.value)
    )
  }
  
  // Фильтр по переводу
  if (selectedTranslation.value) {
    filtered = filtered.filter(movie => 
      movie.translation && movie.translation.includes(selectedTranslation.value)
    )
  }
  
  // Сортировка
  filtered.sort((a, b) => {
    switch (sortBy.value) {
      case 'year':
        return b.year - a.year
      case 'rating':
        const ratingA = Math.max(a.imdbRating || 0, a.kpRating || 0)
        const ratingB = Math.max(b.imdbRating || 0, b.kpRating || 0)
        return ratingB - ratingA
      case 'title':
        return a.title.localeCompare(b.title)
      default:
        return 0
    }
  })
  
  return filtered
})

// Общее количество страниц
const totalPages = computed(() => {
  const total = Math.max(1, Math.ceil(filteredMovies.value.length / itemsPerPage.value))
  return total
})

// Фильмы для текущей страницы (с "подгрузкой" вперед от выбранной страницы)
const paginatedMovies = computed(() => {
  const clampedPage = Math.min(Math.max(1, currentPage.value), totalPages.value)
  const start = Math.max(0, (clampedPage - pagesLoaded.value) * itemsPerPage.value)
  const end = clampedPage * itemsPerPage.value
  return filteredMovies.value.slice(start, end)
})

// Проверяем есть ли еще элементы для загрузки
const hasMoreItems = computed(() => {
  return currentPage.value < totalPages.value
})

// Видимые страницы пагинации
const visiblePages = computed(() => {
  const pages = []
  const start = Math.max(1, currentPage.value - 2)
  const end = Math.min(totalPages.value, start + 4)
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  // Добавляем многоточие и последнюю страницу если нужно
  if (end < totalPages.value && totalPages.value > 10) {
    if (end < totalPages.value - 1) {
      pages.push('...')
    }
    pages.push(totalPages.value)
  }
  
  return pages
})

// Методы
const applyFilters = () => {
  currentPage.value = 1
  pagesLoaded.value = 1
}

const loadMore = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value += 1
    pagesLoaded.value = Math.min(pagesLoaded.value + 1, currentPage.value)
  }
}

const goToPage = (page) => {
  const target = Math.min(Math.max(1, page), totalPages.value)
  currentPage.value = target
  pagesLoaded.value = 1
  // Прокрутка наверх
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Обработка параметров URL
const handleUrlParams = () => {
  if (route.query.year) {
    selectedYear.value = route.query.year
  } else {
    selectedYear.value = ''
  }
  if (route.query.genre) {
    selectedGenre.value = route.query.genre
  } else {
    selectedGenre.value = ''
  }
  if (route.query.country) {
    selectedCountry.value = decodeURIComponent(route.query.country)
  } else {
    selectedCountry.value = ''
  }
  if (route.query.translation) {
    selectedTranslation.value = decodeURIComponent(route.query.translation)
  } else {
    selectedTranslation.value = ''
  }
  specialFilter.value = route.query.special ? String(route.query.special) : ''
}

onMounted(() => {
  handleUrlParams()
})

watch(() => route.query, () => {
  handleUrlParams()
  applyFilters()
})

// Следим за изменением количества страниц, чтобы не допускать выхода за пределы
watch(totalPages, (newTotal) => {
  if (currentPage.value > newTotal) {
    currentPage.value = newTotal
  }
  if (currentPage.value < 1) {
    currentPage.value = 1
  }
  if (pagesLoaded.value > currentPage.value) {
    pagesLoaded.value = currentPage.value
  }
})
</script>

<style scoped>
.filters {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: nowrap;
}

.filter-select {
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  color: #333;
  min-width: 140px;
  font-size: 14px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.filter-select:hover {
  border-color:rgb(56, 190, 56);
}

.filter-select:focus {
  outline: none;
  border-color:rgb(56, 190, 56);  
  box-shadow: 0 0 0 2px rgba(56, 190, 56, 0.2);
}

.page-nav__btn {
  cursor: pointer;
  padding: 8px;
  margin: 0 4px;
}

.page-nav__btn:hover {
  background: rgba(0,0,0,0.1);
  border-radius: 4px;
}

.btn {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  color: #333;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  display: inline-block;
}

.btn:hover {
  border-color:rgb(56, 190, 56);
  background:rgb(56, 190, 56);
  color: white;
}

.btn-primary {
  background:rgb(61, 184, 61);
  color: white;
  border-color:rgb(56, 190, 56);
}

.btn-secondary {
  background: white;
  color: #333;
  border-color: #ddd;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 14px;
}
</style>