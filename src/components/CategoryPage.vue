<template>
  <section class="sect">
    <div class="section__header d-flex ai-center r-gap-20 c-gap-20">
      <h1 class="section__title flex-1">{{ categoryTitle }}</h1>

      <div class="filters d-flex c-gap-10">
        <select
          v-model="selectedYear"
          @change="applyFilters"
          class="filter-select"
        >
          <option value="">Все годы</option>
          <option v-for="year in availableYears" :key="year" :value="year">
            {{ year }}
          </option>
        </select>

        <select
          v-model="selectedGenre"
          @change="applyFilters"
          class="filter-select"
        >
          <option value="">Все жанры</option>
          <option v-for="genre in availableGenres" :key="genre" :value="genre">
            {{ genre }}
          </option>
        </select>

        <select v-model="sortBy" @change="applyFilters" class="filter-select">
          <option value="year">По году</option>
          <option value="rating">По рейтингу</option>
          <option value="popularity">По популярности</option>
          <option value="title">По названию</option>
        </select>
      </div>
    </div>

    <div class="section__content grid-items" id="grid-items">
      <ItemsChunk
        v-for="(pageItems, idx) in pages"
        :key="`chunk-${idx}`"
        :items="pageItems"
      />
      <div v-if="isLoading && shownCount === 0" class="category__loader">
        Загрузка…
      </div>
      <div v-if="error" class="category__error">
        Не удалось загрузить данные. Попробуйте обновить страницу.
      </div>
    </div>

    <div class="pagination ignore-select d-flex jc-center" id="pagination">
      <div
        v-if="hasMoreItems"
        class="page-nav__btn-loader d-flex jc-center ai-center w-100"
      >
        <a href="#" @click.prevent="loadMore" :class="{ disabled: isLoading }">
          <span class="fal fa-redo"></span>
          {{ isLoading ? "Загружаем…" : "Загрузить еще" }}
        </a>
      </div>

      <div v-if="totalPages > 1" class="page-nav__pages d-flex jc-center">
        <span
          @click="goToPage(currentPage - 1)"
          v-if="currentPage > 1"
          class="page-nav__btn"
        >
          <i class="page-nav__btn--prev fal утраarrow-left"></i>
        </span>

        <div class="page-nav__pages d-flex jc-center">
          <span v-for="page in visiblePages" :key="page">
            <span v-if="page === '...'" class="nav_ext">{{ page }}</span>
            <span v-else-if="page === currentPage">{{ page }}</span>
            <a v-else href="#" @click.prevent="goToPage(page)">{{ page }}</a>
          </span>
        </div>

        <span
          @click="goToPage(currentPage + 1)"
          v-if="currentPage < totalPages"
          class="page-nav__btn"
        >
          <i class="page-nav__btn--next fal fa-arrow-right"></i>
        </span>
      </div>
    </div>
  </section>
</template>

<script setup>
import {
  ref,
  computed,
  watch,
  onMounted,
  onBeforeUnmount,
  inject,
  shallowRef,
} from "vue";
import { useRoute, useRouter } from "vue-router";
import ItemsChunk from "./ItemsChunk.vue";

const props = defineProps({ category: String });
const route = useRoute();
const router = useRouter();

const injected =
  typeof window === "undefined" ? inject("categoryFeed", null) : null;
const initialFeed =
  typeof window === "undefined"
    ? injected
    : (window.__CATEGORY_FEED__ && window.__CATEGORY_FEED__[props.category]) ||
      null;

const pages = shallowRef(initialFeed?.items ? [initialFeed.items] : []);
const categoryTitle = ref(initialFeed?.title || "Контент");
const availableYears = ref(initialFeed?.availableYears || []);
const availableGenres = ref(initialFeed?.availableGenres || []);
const total = ref(initialFeed?.total || 0);
const totalPages = ref(initialFeed?.totalPages || 1);
const currentPage = ref(initialFeed?.page || 1);
const shownCount = computed(() =>
  pages.value.reduce((n, arr) => n + (arr?.length || 0), 0)
);
const hasMoreItems = computed(() => shownCount.value < total.value);

const itemsPerPage = 24;

const selectedYear = ref(route.query.year || "");
const selectedGenre = ref(route.query.genre || "");
const selectedCountry = ref(
  route.query.country ? decodeURIComponent(route.query.country) : ""
);
const selectedTranslation = ref(
  route.query.translation ? decodeURIComponent(route.query.translation) : ""
);
const selectedActor = ref(
  route.query.actor ? decodeURIComponent(route.query.actor) : ""
);
const sortBy = ref(route.query.sort || "year");
const specialFilter = ref(
  route.query.special ? String(route.query.special) : ""
);

const isLoading = ref(false);
const error = ref(null);
const abortCtrl = ref(null);
let reqId = 0;
let debounceTimer = null;
let lastFetchKey = ""; // ключ последнего успешного запроса

const visiblePages = computed(() => {
  const totalLen = totalPages.value;
  const current = Math.min(Math.max(1, currentPage.value), totalLen);
  if (totalLen <= 10) return Array.from({ length: totalLen }, (_, i) => i + 1);

  const pages = [];
  const windowSize = 5;
  let start = Math.max(2, current - Math.floor(windowSize / 2));
  let end = Math.min(totalLen - 1, start + windowSize - 1);
  start = Math.max(2, Math.min(start, totalLen - 1 - (windowSize - 1)));
  end = Math.min(totalLen - 1, start + windowSize - 1);

  pages.push(1);
  if (start > 2) pages.push("...");
  for (let i = start; i <= end; i++) pages.push(i);
  if (end < totalLen - 1) pages.push("...");
  pages.push(totalLen);

  return pages;
});

function buildParams(page) {
  const params = new URLSearchParams({
    name: props.category,
    page: String(page),
    limit: String(itemsPerPage),
    sort: sortBy.value,
  });
  if (selectedYear.value) params.set("year", selectedYear.value);
  if (selectedGenre.value) params.set("genre", selectedGenre.value);
  if (selectedCountry.value) params.set("country", selectedCountry.value);
  if (selectedTranslation.value)
    params.set("translation", selectedTranslation.value);
  if (selectedActor.value) params.set("actor", selectedActor.value);
  if (specialFilter.value) params.set("special", specialFilter.value);
  return params;
}

async function fetchCategory({ page = 1, append = false } = {}) {
  // отменяем предыдущий запрос
  try {
    abortCtrl.value?.abort();
  } catch {}
  const myCtrl = new AbortController();
  abortCtrl.value = myCtrl;
  const myReq = ++reqId;

  // дедупликация одинаковых запросов (без append)
  const key = `${props.category}?${buildParams(page).toString()}`;
  if (!append && key === lastFetchKey) return;

  try {
    isLoading.value = true;
    error.value = null;

    const resp = await fetch(`/api/category?${buildParams(page).toString()}`, {
      signal: myCtrl.signal,
    });
    if (!resp.ok) throw new Error("category-fetch-failed");

    const data = await resp.json();
    // игнорируем устаревший ответ
    if (myReq !== reqId) return;

    // запоминаем ключ успешного полного запроса
    if (!append) lastFetchKey = key;

    categoryTitle.value = data.title || "Контент";
    availableYears.value = data.availableYears || [];
    availableGenres.value = data.availableGenres || [];
    total.value = data.total || 0;
    totalPages.value = data.totalPages || 1;

    if (append) {
      pages.value = [...pages.value, data.items || []];
      currentPage.value = data.page || currentPage.value + 1;
    } else {
      pages.value = [data.items || []];
      currentPage.value = data.page || 1;
    }

    // Обновляем кэш для текущей категории
    if (typeof window !== 'undefined') {
      window.__CATEGORY_FEED__ = window.__CATEGORY_FEED__ || {}
      window.__CATEGORY_FEED__[props.category] = data
    }
  } catch (e) {
    if (e?.name === "AbortError") return;
    error.value = e;
  } finally {
    if (myReq === reqId) isLoading.value = false;
  }
}

function pushFiltersToUrl(page = 1) {
  const query = {};
  if (selectedYear.value) query.year = selectedYear.value;
  if (selectedGenre.value) query.genre = selectedGenre.value;
  if (selectedCountry.value) query.country = selectedCountry.value;
  if (selectedTranslation.value) query.translation = selectedTranslation.value;
  if (selectedActor.value) query.actor = selectedActor.value;
  if (sortBy.value && sortBy.value !== "year") query.sort = sortBy.value;
  if (specialFilter.value) query.special = String(specialFilter.value);
  if (page && page !== 1) query.page = String(page);
  router.replace({ path: `/${props.category}`, query });
}
function applyFilters() {
  // Debounce для предотвращения слишком частых запросов
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    pushFiltersToUrl(1);
  }, 150) // 150ms задержка
}
function goToPage(page) {
  const target = Math.min(Math.max(1, page), totalPages.value);
  if (target === currentPage.value) return;
  pushFiltersToUrl(target);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

onBeforeUnmount(() => {
  try {
    abortCtrl.value?.abort();
  } catch {}
  if (debounceTimer) clearTimeout(debounceTimer)
});
function loadMore() {
  if (!hasMoreItems.value || isLoading.value) return;
  fetchCategory({ page: currentPage.value + 1, append: true });
}
function handleUrlParams() {
  selectedYear.value = route.query.year || "";
  selectedGenre.value = route.query.genre || "";
  selectedCountry.value = route.query.country
    ? decodeURIComponent(route.query.country)
    : "";
  selectedTranslation.value = route.query.translation
    ? decodeURIComponent(route.query.translation)
    : "";
  selectedActor.value = route.query.actor
    ? decodeURIComponent(route.query.actor)
    : "";
  sortBy.value = route.query.sort || "year";
  specialFilter.value = route.query.special ? String(route.query.special) : "";
}

onMounted(() => {
  if (!initialFeed) fetchCategory({ page: 1 });
});

// Главное исправление: реакция на смену категории
watch(() => props.category, (newCategory, oldCategory) => {
  if (newCategory !== oldCategory) {
    // Полная очистка состояния при смене категории
    pages.value = []
    total.value = 0
    totalPages.value = 1
    currentPage.value = 1
    error.value = null
    lastFetchKey = "" // сбросить ключ, чтобы избежать пропуска загрузки

    // Очистка фильтров до default значений
    selectedYear.value = route.query.year || ''
    selectedGenre.value = route.query.genre || ''
    selectedCountry.value = route.query.country ? decodeURIComponent(route.query.country) : ''
    selectedTranslation.value = route.query.translation ? decodeURIComponent(route.query.translation) : ''
    selectedActor.value = route.query.actor ? decodeURIComponent(route.query.actor) : ''
    sortBy.value = route.query.sort || 'year'
    specialFilter.value = route.query.special ? String(route.query.special) : ''

    // Перезагрузка данных для новой категории
    const p = Math.max(1, parseInt(route.query.page, 10) || 1)
    fetchCategory({ page: p, append: false })
  }
})

watch(
  () => route.query,
  () => {
    handleUrlParams();
    const p = Math.max(1, parseInt(route.query.page, 10) || 1);
    fetchCategory({ page: p, append: false });
  }
);
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
  border-color: rgb(56, 190, 56);
}

.filter-select:focus {
  outline: none;
  border-color: rgb(56, 190, 56);
  box-shadow: 0 0 0 2px rgba(56, 190, 56, 0.2);
}

.category__loader,
.category__error {
  width: 100%;
  text-align: center;
  padding: 40px 0;
  color: #666;
}

.page-nav__btn-loader a.disabled {
  pointer-events: none;
  opacity: 0.6;
}
</style>
