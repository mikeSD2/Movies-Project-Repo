<template>
  <section class="sect">
    <div class="sect___header d-flex ai-center r-gap-20 c-gap-20">
      <h1 class="sect___title flex-1">{{ pageTitle }}</h1>

      <div class="filters d-flex c-gap-10">
        <select
          v-model="selectedYear"
          @change="applyFilters"
          class="filter-select filter--year"
        >
          <option value="">Все годы</option>
          <option v-for="year in availableYears" :key="year" :value="year">
            {{ year }}
          </option>
        </select>

        <select
          v-model="selectedGenre"
          @change="applyFilters"
          class="filter-select filter--genre"
        >
          <option value="">Все жанры</option>
          <option v-for="genre in availableGenres" :key="genre" :value="genre">
            {{ genre }}
          </option>
        </select>

        <select
          v-model="sortBy"
          @change="applyFilters"
          class="filter-select filter--sort"
        >
          <option value="year">По году</option>
          <option value="rating">По рейтингу</option>
          <option value="popularity">По популярности</option>
          <option value="title">По названию</option>
        </select>
      </div>
    </div>

    <div class="sect___content items-in-grid" id="items-in-grid">
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
          <i class="page-nav__btn--prev fal fa-arrow-left"></i>
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
import {
  setMeta,
  setOg,
  setCanonical,
  setTwitter,
} from "../assets/seoUtils.js";

function getCategoryFallbackTitle(slug) {
  const map = {
    filmy: "Фильмы",
    films: "Фильмы",
    serialy: "Сериалы",
    serials: "Сериалы",
    anime: "Аниме",
    animes: "Аниме",
    multfilmy: "Мультфильмы",
    multfilm: "Мультфильмы",
    cartoons: "Мультфильмы",
  };
  return map[slug] || "Фильмы и сериалы";
}

function normalizeTitle(title, slug) {
  const t = String(title || "").trim();
  return !t || t.toLowerCase() === "контент"
    ? getCategoryFallbackTitle(slug)
    : t;
}

const pageTitle = computed(() => {
  const base = categoryTitle.value; // уже во множественном числе, типа "Фильмы", "Сериалы"
  const g = selectedGenre.value;
  const y = selectedYear.value || new Date().getFullYear();
  if (g) {
    return `${base} жанра ${g} ${y} смотреть онлайн бесплатно`;
  }
  return `${base} список смотреть онлайн бесплатно`;
});

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

const EXCLUDED_GENRES = new Set(
  [
    "Фильмы 2025 года",
    "Фильм-нуар",
    "Сверхъестественное",
    "Молодость",
    "Концерт",
    "Фильмы",
    // добавляйте свои исключения тут
  ].map(normalizeGenreLabel)
);

const pages = shallowRef(initialFeed?.items ? [initialFeed.items] : []);
const categoryTitle = ref(normalizeTitle(initialFeed?.title, props.category));
const availableYears = ref(initialFeed?.availableYears || []);
const availableGenres = ref(
  (initialFeed?.availableGenres || []).filter(
    (g) => !EXCLUDED_GENRES.has(normalizeGenreLabel(g))
  )
);
const total = ref(initialFeed?.total || 0);
const totalPages = ref(initialFeed?.totalPages || 1);
const currentPage = ref(initialFeed?.page || 1);
const shownCount = computed(() =>
  pages.value.reduce((n, arr) => n + (arr?.length || 0), 0)
);
const hasMoreItems = computed(
  () => currentPage.value < totalPages.value && shownCount.value < total.value
);

const itemsPerPage = 24;

const selectedYear = ref(route.query.year || "");
const selectedGenre = ref(
  route.query.genre ? normalizeGenreLabel(route.query.genre) : ""
);
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

const isNarrow = ref(false);
onMounted(() => {
  if (typeof window !== "undefined") {
    const mq = window.matchMedia("(max-width: 600px)");
    const apply = (e) => (isNarrow.value = !!e.matches);
    apply(mq);
    mq.addEventListener("change", apply);
    onBeforeUnmount(() => mq.removeEventListener("change", apply));
  }
});

const visiblePages = computed(() => {
  const totalLen = totalPages.value;
  const current = Math.min(Math.max(1, currentPage.value), totalLen);
  if (totalLen <= 10) return Array.from({ length: totalLen }, (_, i) => i + 1);

  const pages = [];
  const windowSize = isNarrow.value ? 3 : 5; // <-- здесь ключевое
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

function updateCategorySeo() {
  if (typeof window === "undefined") return;
  const origin = window.location.origin;
  const cat = props.category;

  const forms = {
    filmy: { gen: "фильмов", lower: "фильмы" },
    serialy: { gen: "сериалов", lower: "сериалы" },
    multfilmy: { gen: "мультфильмов", lower: "мультфильмы" },
    anime: { gen: "аниме", lower: "аниме" },
  };
  const f = forms[cat] || { gen: "контента", lower: "контент" };

  const q = route.query || {};
  const qual = [];
  if (q.genre) qual.push(`жанра ${normalizeGenreLabel(q.genre)}`);
  if (q.country) qual.push(`страны ${decodeURIComponent(q.country)}`);
  if (q.year) qual.push(`за ${q.year} год`);
  if (q.translation)
    qual.push(`в переводе ${decodeURIComponent(q.translation)}`);

  let listGen = f.gen;
  let lowerNom = f.lower;
  if (q.special === "doramas") {
    listGen = "дорам";
    lowerNom = "дорамы";
  } else if (q.special === "turkish") {
    listGen = "турецких сериалов";
    lowerNom = "турецкие сериалы";
  }
  if (q.actor) qual.unshift(`с ${decodeURIComponent(q.actor)}`);

  const qualStr = qual.length ? ` ${qual.join(", ")}` : "";
  const title = `Список всех ${listGen}${qualStr} смотреть онлайн бесплатно в хорошем качестве на ProsmotrZone`;
  const desc = `Выбирайте для просмотра ${lowerNom}${qualStr} с помощью удобных фильтров и смотрите в HD качестве без регистрации онлайн на ProsmotrZone.`;
  const usp = new URLSearchParams(window.location.search);
  if ((usp.get("page") || "1") === "1") usp.delete("page");
  if ((usp.get("limit") || "24") === "24") usp.delete("limit");
  if ((usp.get("sort") || "year") === "year") usp.delete("sort");

  const url = `${origin}/${cat}${usp.toString() ? `?${usp.toString()}` : ""}`;
  const logoAbs = `${origin}/assets/ProsmotrZone_site/images/NewLogo.webp`;

  document.title = title;
  setCanonical(url);
  const outOfRange = currentPage.value > totalPages.value;
  setMeta(
    "robots",
    total.value > 0 && !outOfRange ? "index,follow" : "noindex,follow"
  );
  setMeta("description", desc);
  setOg("og:url", url);
  setOg("og:type", "website");
  setOg("og:title", title);
  setOg("og:description", desc);
  setOg("og:image", logoAbs);
  setTwitter("twitter:card", "summary_large_image");
  setTwitter("twitter:title", title);
  setTwitter("twitter:description", desc);
  setTwitter("twitter:image", logoAbs);
}
onMounted(updateCategorySeo);
watch([() => props.category, () => route.query], updateCategorySeo);

function normalizeGenreLabel(s) {
  const key = String(s || "")
    .trim()
    .toLowerCase();
  const MAP = {
    триллер: "Триллер",
    триллеры: "Триллер",

    ужасы: "Ужасы",
    ужас: "Ужасы",
    хоррор: "Ужасы",
    horror: "Ужасы",

    комедия: "Комедия",
    комедии: "Комедия",

    драма: "Драма",
    драмы: "Драма",

    детектив: "Детектив",
    детективы: "Детектив",

    детский: "Детский",
    детские: "Детский",

    фантастика: "Фантастика",
    "sci-fi": "Фантастика",
    "научная фантастика": "Фантастика",

    фэнтези: "Фэнтези",
    фентези: "Фэнтези",

    боевик: "Боевик",
    боевики: "Боевик",

    приключения: "Приключения",
    приключение: "Приключения",

    мелодрама: "Мелодрама",
    мелодрамы: "Мелодрама",

    криминал: "Криминал",

    военный: "Военный",
    военные: "Военный",
    военная: "Военный",
    военное: "Военный",
    war: "Военный",
    military: "Военный",

    документальный: "Документальные",

    вестерны: "Вестерн",

    мюзикл: "Мюзиклы",
    музыка: "Мюзиклы",

    спортивные: "Спорт",
    спортивный: "Спорт",
    sport: "Спорт",
    sports: "Спорт",
    cпортивные: "Спорт", // латинская 'c' в начале

    детское: "Детский",

    экшен: "Боевик",

    пародия: "Пародия",
    короткометражка: "Короткометражка",
    мультсериал: "Мультсериал",

    вестерн: "Вестерн", // вместе с уже существующим 'вестерны'
    биография: "Биография",

    биографии: "Биография",
    биографические: "Биография",

    история: "История",
    исторический: "История",
    исторические: "История",

    семейный: "Семейный",
    семейные: "Семейный",

    спорт: "Спорт",
    аниме: "Аниме",
    мультфильмы: "Мультфильмы",
    мультфильм: "Мультфильмы",
    дорама: "Дорамы",
    дорамы: "Дорамы",
    "турецкие сериалы": "Турецкие сериалы",
  };
  if (MAP[key]) return MAP[key];
  return key ? key[0].toUpperCase() + key.slice(1) : "";
}

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

    const normalized = normalizeTitle(data.title, props.category);
    categoryTitle.value = normalized;
    availableYears.value = data.availableYears || [];
    availableGenres.value = (data.availableGenres || []).filter(
      (g) => !EXCLUDED_GENRES.has(normalizeGenreLabel(g))
    );
    total.value = data.total || 0;
    totalPages.value = data.totalPages || 1;

    if (append) {
      pages.value = [...pages.value, data.items || []];
      currentPage.value = data.page || currentPage.value + 1;
    } else {
      pages.value = [data.items || []];
      currentPage.value = data.page || 1;
    }

    // Обновляем кэш для текущей категории (с нормализованным title)
    if (typeof window !== "undefined") {
      window.__CATEGORY_FEED__ = window.__CATEGORY_FEED__ || {};
      window.__CATEGORY_FEED__[props.category] = { ...data, title: normalized };
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
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    pushFiltersToUrl(1);
  }, 150); // 150ms задержка
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
  if (debounceTimer) clearTimeout(debounceTimer);
});
function loadMore() {
  if (
    isLoading.value ||
    currentPage.value >= totalPages.value ||
    !hasMoreItems.value
  )
    return;
  fetchCategory({ page: currentPage.value + 1, append: true });
}
function handleUrlParams() {
  selectedYear.value = route.query.year || "";
  selectedGenre.value = route.query.genre
    ? normalizeGenreLabel(route.query.genre)
    : "";
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
  const curr = String(categoryTitle.value || "")
    .trim()
    .toLowerCase();
  if (!initialFeed || !curr || curr === "контент") {
    fetchCategory({ page: 1 });
  }
});

// Главное исправление: реакция на смену категории
watch(
  () => props.category,
  (newCategory, oldCategory) => {
    if (newCategory !== oldCategory) {
      // Полная очистка состояния при смене категории
      pages.value = [];
      total.value = 0;
      totalPages.value = 1;
      currentPage.value = 1;
      error.value = null;
      lastFetchKey = ""; // сбросить ключ, чтобы избежать пропуска загрузки

      // Очистка фильтров до default значений
      selectedYear.value = route.query.year || "";
      selectedGenre.value = route.query.genre
        ? normalizeGenreLabel(route.query.genre)
        : "";
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
      specialFilter.value = route.query.special
        ? String(route.query.special)
        : "";

      // Перезагрузка данных для новой категории
      const p = Math.max(1, parseInt(route.query.page, 10) || 1);
      fetchCategory({ page: p, append: false });
    }
  }
);

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

@media (max-width: 600px) {
  .sect___header {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .filters {
    margin-left: 0;
    width: 100%;
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-areas:
      "year sort"
      "genre genre";
    gap: 10px;
  }

  .filter--year {
    grid-area: year;
  }
  .filter--sort {
    grid-area: sort;
  }
  .filter--genre {
    grid-area: genre;
  }

  .filter-select {
    min-width: 0;
    width: 100%;
  }
}
/* Пагинация: исправления только для CategoryPage (scoped) */

/* Разнести "Загрузить ещё" и пагинацию по вертикали и убрать переносы */
.pagination {
  flex-direction: column; /* перекрывает .d-flex (row) */
  flex-wrap: nowrap; /* отменяем wrap на контейнере */
  align-items: center;
}

/* Кнопки страниц — в одну строку без переноса */
.pagination .page-nav__pages.d-flex {
  flex-wrap: nowrap; /* перекрывает .d-flex { flex-wrap: wrap } */
  white-space: nowrap; /* подстраховка от переноса */
}

/* Мобильные уточнения: ужимаем размеры, чтобы всё влезало в 1 строку */
@media (max-width: 600px) {
  /* Кнопка "Загрузить ещё": не даём ей фиксированный min-width из глобальных стилей */
  .page-nav__btn-loader a {
    min-width: 0;
    width: 100%;
  }

  /* Чуть уменьшаем размеры и расстояния у кнопок страниц */
  .pagination .page-nav__pages {
    gap: 6px;
  }
  .pagination .page-nav__pages a,
  .pagination .page-nav__pages span,
  .pagination > a,
  .pagination > span {
    min-width: 30px; /* было 36px в глобальных */
    height: 32px; /* было 36px */
    font-size: 13px; /* слегка меньше, чтобы поместилось без wrap */
  }
}

/* Совсем узкие экраны — ещё компактнее */
@media (max-width: 380px) {
  .pagination .page-nav__pages {
    gap: 4px;
  }
  .pagination .page-nav__pages a,
  .pagination .page-nav__pages span,
  .pagination > a,
  .pagination > span {
    min-width: 28px;
    height: 30px;
    font-size: 12px;
  }
}
/* Внешний контейнер стрелки+цифры: по центру и с небольшим зазором (десктоп) */
.pagination > .page-nav__pages.d-flex {
  width: 100%;
  box-sizing: border-box;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: center; /* было space-between — вернули центр */
  gap: 10px; /* чтобы стрелки были рядом с цифрами */
}

/* Средний блок с цифрами: НЕ растёт на десктопе (чтобы стрелки прилегали) */
.pagination > .page-nav__pages.d-flex > .page-nav__pages.d-flex {
  flex: 0 1 auto; /* десктоп: не растём, допускаем сжатие */
  min-width: 0;
  justify-content: center;
  flex-wrap: nowrap;
  white-space: nowrap;
}

/* Стрелки — фикс. ширина, не растягиваются */
.pagination .page-nav__btn {
  flex: 0 0 auto;
}

/* Мобильные уточнения — сохраняем поведение, чтобы ничего не вылезало */
@media (max-width: 600px) {
  /* На мобиле — разнос, чтобы гарантированно всё помещалось */
  .pagination > .page-nav__pages.d-flex {
    justify-content: space-between;
  }
  /* На мобиле цифры могут сжиматься и занимать центр */
  .pagination > .page-nav__pages.d-flex > .page-nav__pages.d-flex {
    flex: 1 1 auto; /* мобильное поведение из прошлой правки */
  }

  .page-nav__btn-loader a {
    /* кнопка "Загрузить ещё" — на всю ширину */
    min-width: 0;
    width: 100%;
  }

  .pagination .page-nav__pages {
    gap: 6px;
  }
  .pagination .page-nav__pages a,
  .pagination .page-nav__pages span,
  .pagination > a,
  .pagination > span {
    min-width: 30px;
    height: 32px;
    font-size: 13px;
  }
  .pagination .page-nav__btn {
    min-width: 28px;
  }
}

.pagination .page-nav__btn {
  cursor: pointer;
}
</style>
