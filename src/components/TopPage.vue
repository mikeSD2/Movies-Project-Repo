<!-- src/components/TopPage.vue -->
<template>
  <div class="items-in-grid count-items">
    <section class="sect ignore-select">
      <div class="sect___header d-flex ai-center">
        <h1 class="sect___title flex-1">
          {{ h1Title }}
        </h1>
        <div class="filters d-flex c-gap-10" style="margin-left: auto">
          <select
            class="filter-select"
            v-model="topType"
            @change="onTypeChange($event.target.value)"
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

      <div class="sect___content items-in-grid">
        <MovieCard v-for="movie in filtered" :key="movie.id" :movie="movie" />
        <div v-if="loading && filtered.length === 0" class="tops__loader">
          Загрузка…
        </div>
      </div>

      <div class="pagination ignore-select d-flex jc-center" v-if="hasMore()">
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
import { computed, onMounted, watch, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import MovieCard from "./MovieCard.vue";
import { useTopInfinite } from "../assets/useTopInfinite.js";
import {
  setMeta,
  setOg,
  setCanonical,
  setTwitter,
} from "../assets/seoUtils.js";

const route = useRoute();
const router = useRouter();
const { items, hasMore, loading, loadMore, setType, type } = useTopInfinite();
const filtered = computed(() => items.value);
const topType = ref("all");

const typeLabel = computed(() => {
  const map = {
    all: "фильмы, сериалы и мультфильмы",
    filmy: "фильмы",
    serialy: "сериалы",
    multfilmy: "мультфильмы",
    anime: "аниме",
    doramas: "дорамы",
    turkish: "турецкие сериалы",
  };
  return map[topType.value] || "фильмы, сериалы и мультфильмы";
});
const h1Title = computed(() =>
  topType.value === "all"
    ? "Топ за все время: фильмы, сериалы и мультфильмы"
    : `Топ за все время: ${typeLabel.value}`
);

function updateTopSeo() {
  if (typeof window === "undefined") return;
  const origin = window.location.origin;
  const logoAbs = `${origin}/assets/ProsmotrZone_site/images/NewLogo.webp`;
  const title =
    topType.value === "all"
      ? "Топ всех фильмов и сериалов на ProsmotrZone. Выбирайте и смотрите!"
      : `Топ: ${typeLabel.value} — ProsmotrZone`;
  const desc =
    "Лучшие фильмы и сериалы по рейтингу IMDb и Кинопоиск на ProsmotrZone. Выбирайте и смотрите онлайн бесплатно в HD.";
  document.title = title;
  setCanonical(origin + "/top-all-time"); // canonical фиксированный
  setMeta("robots", "index,follow");
  setMeta("description", desc);
  setOg("og:type", "website");
  setOg("og:title", title);
  setOg("og:description", desc);
  setOg("og:image", logoAbs);
  setOg("og:url", origin + "/top-all-time");
  setTwitter("twitter:card", "summary_large_image");
  setTwitter("twitter:title", title);
  setTwitter("twitter:description", desc);
  setTwitter("twitter:image", logoAbs);
}

function onTypeChange(next) {
  const q = { ...route.query };
  if (!next || next === "all") delete q.type;
  else q.type = next;
  router.replace({ path: "/top-all-time", query: q });
  setType(next);
}

// при монтировании и смене query подхватываем type
watch(
  () => route.query.type,
  (t) => {
    const v = t || "all";
    topType.value = v;
    setType(v);
    updateTopSeo();
  },
  { immediate: true }
);

onMounted(updateTopSeo);
</script>

<style scoped>
.filter-select {
  padding-right: 38px; 
  background-position: right 12px center; 
}
.filter-icon { margin-right: 8px; font-size: 18px; opacity: .85; }
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
@media (max-width: 600px) {
  .sect___header {
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
