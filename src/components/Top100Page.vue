<template>
  <div class="grid-items count-items">
    <section class="sect ignore-select">
      <div class="section__header d-flex ai-center">
        <h1 class="section__title flex-1">Топ всех фильмов и сериалов</h1>

        <div class="filters d-flex c-gap-10">
          <select v-model="selectedType" @change="resetAndApply" class="filter-select">
            <option value="">Все</option>
            <option value="filmy">Фильмы</option>
            <option value="serialy">Сериалы</option>
            <option value="multfilmy">Мультфильмы</option>
            <option value="anime">Аниме</option>
            <option value="doramas">Дорамы</option>
            <option value="turkish">Турецкие сериалы</option>
          </select>
        </div>
      </div>

      <div class="section__content grid-items">
        <MovieCard v-for="movie in paginatedMovies" :key="movie.id" :movie="movie" />
      </div>

      <div class="pagination ignore-select d-flex jc-center" v-if="hasMoreItems">
        <div class="page-nav__btn-loader d-flex jc-center ai-center w-100">
          <a href="#" @click.prevent="loadMore">
            <span class="fal fa-redo"></span>Загрузить еще
          </a>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import MovieCard from './MovieCard.vue'
import moviesData from '../../movies-data.json'

const all = (moviesData.movies || []).filter(m => m.id !== 'index')

const selectedType = ref('')
const itemsPerPage = ref(24)
const currentPage = ref(1)

const isAsian = (countryStr) => {
  if (!countryStr) return false
  const s = String(countryStr).toLowerCase()
  const asianKeywords = [
    'южная корея','корея','северная корея',
    'япония','китай','тайвань','гонконг',
    'таиланд','индонезия','малайзия','вьетнам',
    'сингапур','филиппины'
  ]
  return asianKeywords.some(k => s.includes(k))
}

const ratingOf = (m) => {
  const imdb = typeof m.imdbRating === 'number' ? m.imdbRating : parseFloat(String(m.imdbRating || '').replace(',', '.')) || 0
  const kp = typeof m.kpRating === 'number' ? m.kpRating : parseFloat(String(m.kpRating || '').replace(',', '.')) || 0
  return Math.max(imdb, kp)
}

const filteredSorted = computed(() => {
  let list = [...all]
  switch (selectedType.value) {
    case 'filmy':
    case 'serialy':
    case 'multfilmy':
    case 'anime':
      list = list.filter(m => m.category === selectedType.value)
      break
    case 'doramas':
      list = list.filter(m => m.category === 'serialy' && isAsian(m.country))
      break
    case 'turkish':
      list = list.filter(m => m.category === 'serialy' && /турция/i.test(m.country || ''))
      break
    default:
      break
  }
  return list
    .map(m => ({ movie: m, rating: ratingOf(m) }))
    .filter(x => x.rating > 0)
    .sort((a, b) => b.rating - a.rating)
    .map(x => x.movie)
})

const totalPages = computed(() => {
  const total = Math.max(1, Math.ceil(filteredSorted.value.length / itemsPerPage.value))
  return total
})

const paginatedMovies = computed(() => {
  const end = currentPage.value * itemsPerPage.value
  return filteredSorted.value.slice(0, end)
})

const hasMoreItems = computed(() => {
  return currentPage.value < totalPages.value
})

const loadMore = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value += 1
  }
}

const resetAndApply = () => {
  currentPage.value = 1
}
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
  min-width: 180px;
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
</style>