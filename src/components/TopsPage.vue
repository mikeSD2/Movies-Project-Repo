<template>
  <div class="grid-items count-items">
    <section class="sect ignore-select">
      <div class="section__header d-flex ai-center">
        <h1 class="section__title flex-1">Топ всех фильмов и сериалов</h1>

        <div class="filters d-flex c-gap-10">
          <select
            v-model="selectedType"
            @change="onTypeChange"
            class="filter-select"
          >
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
        <MovieCard
          v-for="movie in filtered"
          :key="movie.id"
          :movie="movie"
        />
        <div
          v-if="loading && filtered.length === 0"
          class="tops__loader"
        >
          Загрузка…
        </div>
      </div>

      <div
        class="pagination ignore-select d-flex jc-center"
        v-if="hasMore()"
      >
        <div class="page-nav__btn-loader d-flex jc-center ai-center w-100">
          <a
            href="#"
            @click.prevent="!loading && loadMore()"
            :class="{ disabled: loading }"
          >
            <span class="fal fa-redo"></span>
            {{ loading ? "Загружаем…" : "Загрузить ещё" }}
          </a>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import MovieCard from './MovieCard.vue'
import { useTopInfinite } from '../assets/useTopInfinite.js'

const selectedType = ref('')
const { items, hasMore, loading, loadMore, setType } = useTopInfinite()

const filtered = computed(() => items.value)

function onTypeChange() {
  setType(selectedType.value || 'all')
}
</script>

<style scoped>
.tops__loader {
  width: 100%;
  padding: 40px 0;
  text-align: center;
  color: #666;
  font-size: 16px;
}
.page-nav__btn-loader a.disabled {
  pointer-events: none;
  opacity: 0.6;
}
</style>
