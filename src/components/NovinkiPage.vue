<template>
  <div class="items-in-grid count-items">
    <section class="sect ignore-select">
      <div class="section--header d-flex ai-center">
        <h1 class="section--title flex-1">
          {{ h1Title }}
        </h1>
        <div class="filters d-flex c-gap-10" style="margin-left: auto">
          <select
            class="filter-select"
            :value="categoryType"
            @change="onCategoryChange($event.target.value)"
          >
            <option value="all">Все категории</option>
            <option value="filmy">Фильмы</option>
            <option value="serialy">Сериалы</option>
            <option value="multfilmy">Мультфильмы</option>
            <option value="anime">Аниме</option>
            <option value="doramas">Дорамы</option>
            <option value="turkish">Турецкие</option>
          </select>
        </div>
      </div>

      <div class="section--content items-in-grid">
        <MovieCard v-for="movie in items" :key="movie.id" :movie="movie" />
        <div v-if="loading && items.length === 0" class="tops__loader">
          Загрузка…
        </div>
      </div>

      <div class="pagination ignore-select d-flex jc-center" v-if="hasMore">
        <div class="Pnavigation--btn-loader d-flex jc-center ai-center w-100">
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
import { computed, ref, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import MovieCard from "./MovieCard.vue";
import {
  setMeta,
  setOg,
  setCanonical,
  setTwitter,
} from "../assets/seoUtils.js";

const route = useRoute();
const router = useRouter();

const items = ref([]);
const total = ref(0);
const page = ref(1);
const limit = 24;
const loading = ref(false);

const categoryType = ref("all"); // all|filmy|serialy|multfilmy|anime|doramas|turkish
const year = ref(new Date().getFullYear());

const hasMore = computed(() => items.value.length < total.value);
const yearTitle = computed(() => year.value);

const categoryLabel = computed(() => {
  const map = {
    all: "все категории",
    filmy: "фильмы",
    serialy: "сериалы",
    multfilmy: "мультфильмы",
    anime: "аниме",
    doramas: "дорамы",
    turkish: "турецкие сериалы",
  };
  return map[categoryType.value] || "все категории";
});
const h1Title = computed(() => {
  return categoryType.value === "all"
    ? `Новинки ${yearTitle.value}: фильмы, сериалы, мультфильмы и аниме`
    : `Новинки ${yearTitle.value}: ${categoryLabel.value}`;
});

function buildUrl(p = page.value) {
  const usp = new URLSearchParams();
  usp.set("page", String(p));
  usp.set("limit", String(limit));
  usp.set("sort", "popularity");
  usp.set("year", String(year.value));
  if (categoryType.value === "doramas" || categoryType.value === "turkish") {
    usp.set("name", "serialy");
    usp.set("special", categoryType.value); // doramas|turkish
    return `/api/category?${usp.toString()}`;
  }
  if (categoryType.value && categoryType.value !== "all") {
    usp.set("category", categoryType.value);
  }
  return `/api/movies?${usp.toString()}`;
}

async function fetchPage(p, append = false) {
  loading.value = true;
  try {
    const resp = await fetch(buildUrl(p));
    if (!resp.ok) throw new Error("novinki-fetch-failed");
    const data = await resp.json(); // { items, total, page, totalPages }
    total.value = data.total || 0;
    page.value = data.page || p;
    items.value = append
      ? items.value.concat(data.items || [])
      : data.items || [];
  } finally {
    loading.value = false;
  }
}

function resetAndLoad() {
  items.value = [];
  total.value = 0;
  page.value = 1;
  fetchPage(1, false);
}

function loadMore() {
  if (loading.value || !hasMore.value) return;
  fetchPage(page.value + 1, true);
}

// sync из URL: /novinki?year=2025&category=filmy
function syncFromRoute() {
  const y = parseInt(route.query.year, 10);
  year.value = Number.isFinite(y) ? y : new Date().getFullYear();
  const cat = String(route.query.category || "all");
  categoryType.value = [
    "filmy",
    "serialy",
    "multfilmy",
    "anime",
    "doramas",
    "turkish",
  ].includes(cat)
    ? cat
    : "all";
}
watch(
  () => route.query,
  () => {
    const prevCat = categoryType.value;
    const prevYear = year.value;
    syncFromRoute();
    if (prevCat !== categoryType.value || prevYear !== year.value) {
      resetAndLoad();
    }
  },
  { immediate: false }
);

onMounted(() => {
  syncFromRoute();
  resetAndLoad();
  updateNovinkiSeo();
});

watch([categoryType, year], () => {
  updateNovinkiSeo();
});

function updateNovinkiSeo() {
  if (typeof window === "undefined") return;
  const origin = window.location.origin;
  const logoAbs = `${origin}/assets/NewLord_site/images/logo.svg`;
  const title = `Смотреть онлайн НОВИНКИ мира кино и сериалов ${yearTitle.value} года`;
  const desc = `Свежие новинки ${yearTitle.value} года: ${categoryLabel.value}. Смотрите онлайн бесплатно в хорошем качестве на Lordfilm.`;
  document.title = title;
  setCanonical(origin + "/novinki"); // фиксируем каноникал
  setMeta("robots", "index,follow");
  setMeta("description", desc);
  setOg("og:type", "website");
  setOg("og:title", title);
  setOg("og:description", desc);
  setOg("og:image", logoAbs);
  setOg("og:url", origin + "/novinki");
  setTwitter("twitter:card", "summary_large_image");
  setTwitter("twitter:title", title);
  setTwitter("twitter:description", desc);
  setTwitter("twitter:image", logoAbs);
}

function onCategoryChange(next) {
  const q = { ...route.query };
  if (!next || next === "all") delete q.category;
  else q.category = next;
  router.replace({ path: "/novinki", query: q });
}
</script>

<style scoped>
.filter-icon {
  margin-right: 8px;
  font-size: 18px;
  opacity: 0.85;
}
.tops__loader {
  width: 100%;
  padding: 40px 0;
  text-align: center;
  color: #666;
  font-size: 16px;
}
.Pnavigation--btn-loader a.disabled {
  pointer-events: none;
  opacity: 0.6;
}
.filter-select {
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: white;
  color: #333;
  min-width: 140px;
  font-size: 14px;
  transition: all 0.2s ease;
  cursor: pointer;
  padding-right: 38px; /* было ~30px, увеличиваем расстояние текста до стрелки */
  background-position: right 12px center;
}
.filter-select:hover {
  border-color: rgb(56, 190, 56);
}
.filter-select:focus {
  outline: none;
  border-color: rgb(56, 190, 56);
  box-shadow: 0 0 0 2px rgba(56, 190, 56, 0.2);
}
@media (max-width: 600px) {
  .section--header {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .filters {
    margin-left: 0 !important;
    width: 100%;
  }
  .filter-select {
    min-width: 0;
    width: 100%;
  }
}
</style>
