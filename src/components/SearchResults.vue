<template>
  <div class="grid-items count-items search-results-block" style="padding: 20px;">
    <div class="section__header d-flex ai-center r-gap-20 c-gap-20">
      <h1 class="section__title flex-1">Результаты поиска: "{{ query }}"</h1>
      <button @click="$emit('close')" class="btn">Закрыть</button>
    </div>
    
    <div v-if="results.length === 0" class="no-results">
      <p>По вашему запросу ничего не найдено.</p>
    </div>
    
    <div v-else>
      <div class="section__content grid-items" @click="handleMovieClick">
        <MovieCard 
          v-for="movie in paginatedResults" 
          :key="movie.id" 
          :movie="movie" 
        />
      </div>
      <div v-if="hasMoreResults" class="pagination ignore-select d-flex jc-center">
        <div class="page-nav__btn-loader d-flex jc-center ai-center w-100">
          <a @click.prevent="loadMore" href="#" class="js-search-load-more">
            <span class="fal fa-redo"></span>Загрузить еще
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import MovieCard from './MovieCard.vue'
import { ref, computed, watch } from 'vue'

const props = defineProps({
  query: String,
  results: Array
})

const emit = defineEmits(['close'])

const ITEMS_PER_PAGE = 24
const visibleCount = ref(ITEMS_PER_PAGE)

const paginatedResults = computed(() => {
  return props.results.slice(0, visibleCount.value)
})

const hasMoreResults = computed(() => {
  return visibleCount.value < props.results.length
})

const loadMore = () => {
  visibleCount.value += ITEMS_PER_PAGE
}

watch(() => props.query, () => {
  visibleCount.value = ITEMS_PER_PAGE
})

const handleMovieClick = (event) => {
  // Проверяем, что клик был по ссылке на фильм
  if (event.target.closest('a[href]')) {
    // Закрываем поиск при переходе на страницу фильма
    emit('close')
  }
}
</script>
