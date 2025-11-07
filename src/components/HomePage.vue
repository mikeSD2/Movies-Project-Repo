<template>
  <!-- Карусель популярных -->
  <div class="carou">
    <div class="carou__caption">Популярные за месяц</div>
    <div class="carou__content carousel-grid" id="top-carou" ref="carousel">
      <MovieCard
        v-for="(movie, idx) in popularMovies"
        :key="movie.id"
        :movie="movie"
        :priority="idx === 0"
      />
    </div>
  </div>

  <!-- Секция фильмов -->
  <section class="sect">
    <div class="sect___header d-flex ai-center c-gap-20">
      <router-link
        to="/filmy"
        class="sect___title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Фильмы</h2>
      </router-link>
      <div class="sect___tabs d-flex c-gap-10">
        <button
          :class="{ 'is-active': moviesTab === 'latest' }"
          @click="moviesTab = 'latest'"
        >
          Последние
        </button>
        <button
          :class="{ 'is-active': moviesTab === 'popular' }"
          :disabled="!!moviesPending"
          @click="requestMoviesTab('popular')"
        >
          <span v-if="moviesPending === 'popular'">Загрузка…</span>
          <span v-else>Популярные</span>
        </button>
        <button
          :class="{ 'is-active': moviesTab === 'rating' }"
          :disabled="!!moviesPending"
          @click="requestMoviesTab('rating')"
        >
          <span v-if="moviesPending === 'rating'">Загрузка…</span>
          <span v-else>По рейтингу</span>
        </button>
      </div>
    </div>
    <div class="sect___content items-in-grid">
      <MovieCard
        v-for="(movie, idx) in displayedMovies"
        :key="movie.id"
        :movie="movie"
        :priority="idx === 0"
      />
    </div>
  </section>

  <!-- Секция сериалов -->
  <section class="sect">
    <div class="sect___header d-flex ai-center c-gap-20">
      <router-link
        to="/serialy"
        class="sect___title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Сериалы</h2>
      </router-link>
      <div class="sect___tabs d-flex c-gap-10">
        <button
          :class="{ 'is-active': seriesTab === 'latest' }"
          @click="seriesTab = 'latest'"
        >
          Последние
        </button>
        <button
          :class="{ 'is-active': seriesTab === 'popular' }"
          :disabled="!!seriesPending"
          @click="requestSeriesTab('popular')"
        >
          <span v-if="seriesPending === 'popular'">Загрузка…</span>
          <span v-else>Популярные</span>
        </button>
        <button
          :class="{ 'is-active': seriesTab === 'rating' }"
          :disabled="!!seriesPending"
          @click="requestSeriesTab('rating')"
        >
          <span v-if="seriesPending === 'rating'">Загрузка…</span>
          <span v-else>По рейтингу</span>
        </button>
      </div>
    </div>
    <div ref="seriesSentinel" class="lazy-sentinel" aria-hidden="true"></div>
    <div class="sect___content items-in-grid" v-if="seriesVisible">
      <MovieCard
        v-for="(series, idx) in displayedSeries"
        :key="series.id"
        :movie="series"
        :priority="idx === 0"
      />
    </div>
  </section>

  <!-- Секция мультфильмов -->
  <section class="sect">
    <div class="sect___header d-flex ai-center c-gap-20">
      <router-link
        to="/multfilmy"
        class="sect___title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Мультфильмы</h2>
      </router-link>
      <div class="sect___tabs d-flex c-gap-10">
        <button
          :class="{ 'is-active': cartoonsTab === 'latest' }"
          @click="cartoonsTab = 'latest'"
        >
          Последние
        </button>
        <button
          :class="{ 'is-active': cartoonsTab === 'popular' }"
          :disabled="!!cartoonsPending"
          @click="requestCartoonsTab('popular')"
        >
          <span v-if="cartoonsPending === 'popular'">Загрузка…</span>
          <span v-else>Популярные</span>
        </button>
        <button
          :class="{ 'is-active': cartoonsTab === 'rating' }"
          :disabled="!!cartoonsPending"
          @click="requestCartoonsTab('rating')"
        >
          <span v-if="cartoonsPending === 'rating'">Загрузка…</span>
          <span v-else>По рейтингу</span>
        </button>
      </div>
    </div>
    <div ref="cartoonsSentinel" class="lazy-sentinel" aria-hidden="true"></div>
    <div class="sect___content items-in-grid" v-if="cartoonsVisible">
      <MovieCard
        v-for="(cartoon, idx) in displayedCartoons"
        :key="cartoon.id"
        :movie="cartoon"
        :priority="idx === 0"
      />
    </div>
  </section>

  <!-- Секция аниме -->
  <section class="sect">
    <div class="sect___header d-flex ai-center c-gap-20">
      <router-link
        to="/anime"
        class="sect___title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Аниме</h2>
      </router-link>
      <div class="sect___tabs d-flex c-gap-10">
        <button
          :class="{ 'is-active': animeTab === 'latest' }"
          @click="animeTab = 'latest'"
        >
          Последние
        </button>
        <button
          :class="{ 'is-active': animeTab === 'popular' }"
          :disabled="!!animePending"
          @click="requestAnimeTab('popular')"
        >
          <span v-if="animePending === 'popular'">Загрузка…</span>
          <span v-else>Популярные</span>
        </button>
        <button
          :class="{ 'is-active': animeTab === 'rating' }"
          :disabled="!!animePending"
          @click="requestAnimeTab('rating')"
        >
          <span v-if="animePending === 'rating'">Загрузка…</span>
          <span v-else>По рейтингу</span>
        </button>
      </div>
    </div>
    <div ref="animeSentinel" class="lazy-sentinel" aria-hidden="true"></div>
    <div class="sect___content items-in-grid" v-if="animeVisible">
      <MovieCard
        v-for="(anime, idx) in displayedAnime"
        :key="anime.id"
        :movie="anime"
        :priority="idx === 0"
      />
    </div>
  </section>

  <!-- Секция дорам -->
  <!-- <section class="sect">
    <div class="sect___header d-flex ai-center c-gap-20">
      <router-link
        to="/serialy?special=doramas"
        class="sect___title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Дорамы</h2>
      </router-link>
      <div class="sect___tabs d-flex c-gap-10">
        <button
          :class="{ 'is-active': doramasTab === 'latest' }"
          @click="doramasTab = 'latest'"
        >
          Последние
        </button>
        <button
          :class="{ 'is-active': doramasTab === 'popular' }"
          :disabled="!!doramasPending"
          @click="requestDoramasTab('popular')"
        >
          <span v-if="doramasPending === 'popular'">Загрузка…</span>
          <span v-else>Популярные</span>
        </button>
        <button
          :class="{ 'is-active': doramasTab === 'rating' }"
          :disabled="!!doramasPending"
          @click="requestDoramasTab('rating')"
        >
          <span v-if="doramasPending === 'rating'">Загрузка…</span>
          <span v-else>По рейтингу</span>
        </button>
      </div>
    </div>
    <div ref="doramasSentinel" class="lazy-sentinel" aria-hidden="true"></div>
    <div class="sect___content items-in-grid" v-if="doramasVisible">
      <MovieCard
        v-for="dorama in displayedDoramas"
        :key="dorama.id"
        :movie="dorama"
      />
    </div>
  </section> -->

  <!-- Секция турецких сериалов -->
  <!-- <section class="sect">
    <div class="sect___header d-flex ai-center c-gap-20">
      <router-link
        to="/serialy?special=turkish"
        class="sect___title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Турецкие сериалы</h2>
      </router-link>
      <div class="sect___tabs d-flex c-gap-10">
        <button
          :class="{ 'is-active': turkishTab === 'latest' }"
          @click="turkishTab = 'latest'"
        >
          Последние
        </button>
        <button
          :class="{ 'is-active': turkishTab === 'popular' }"
          :disabled="!!turkishPending"
          @click="requestTurkishTab('popular')"
        >
          <span v-if="turkishPending === 'popular'">Загрузка…</span>
          <span v-else>Популярные</span>
        </button>
        <button
          :class="{ 'is-active': turkishTab === 'rating' }"
          :disabled="!!turkishPending"
          @click="requestTurkishTab('rating')"
        >
          <span v-if="turkishPending === 'rating'">Загрузка…</span>
          <span v-else>По рейтингу</span>
        </button>
      </div>
    </div>
    <div ref="turkishSentinel" class="lazy-sentinel" aria-hidden="true"></div>
    <div class="sect___content items-in-grid" v-if="turkishVisible">
      <MovieCard v-for="ts in displayedTurkish" :key="ts.id" :movie="ts" />
    </div>
  </section> -->

  <!-- Описание сайта -->
  <section class="descr">
    <h1>
      Ваш персональный доступ в мир кино: смотрите фильмы и сериалы онлайн в
      отличном качестве
    </h1>
    <p>
      Выдался тяжелый день? Иногда все, чего хочется, — это просто выдохнуть и
      включить что-то по-настоящему захватывающее. Для этого мы и работаем. Наш
      онлайн-кинотеатр — это ваш личный портал в тысячи кинопроизведений, причем
      бесплатно и без регистрации.
    </p>
    <p>
      Забудьте о расписаниях и очередях в кассу. Теперь только вы решаете, когда
      начнется сеанс. Просто выбирайте и начинайте смотреть фильмы онлайн в
      любое время, всегда в хорошем качестве. Ваш кинозал открыт круглосуточно:
      вас ждет четкая картинка HD 1080p (или 720p для быстрой загрузки) и чистый
      звук в русской озвучке. А многие новинки кино у нас уже доступны в 4K.
    </p>
    <h2>Огромная коллекция: от вечной классики до хитов 2024 и 2025 годов</h2>
    <p>
      Мы правда гордимся своей коллекцией. Наша главная задача — сделать так,
      чтобы каждый нашел что-то для души.
    </p>
    <p>
      В каталоге есть всё: как популярные зарубежные фильмы, так и душевные
      сериалы и фильмы. Мы собрали лучшие фильмы и сериалы всех эпох. Мы держим
      руку на пульсе, поэтому у нас вы всегда найдете самые громкие новинки кино
      2023, 2024 и даже ожидаемые хиты 2025 года. И конечно, мы не забыли про
      мультфильмы для всей семьи и захватывающее аниме.
    </p>
    <p>Наша гигантская коллекция охватывает все жанры:</p>
    <ul>
      <li>Напряженные боевики и триллеры, от которых стынет кровь.</li>
      <li>Глубокие драмы и мелодрамы, чтобы по-настоящему сопереживать.</li>
      <li>Жуткие ужасы и легкие, искрометные комедии.</li>
      <li>Потрясающие миры фантастики и волшебного фэнтези.</li>
      <li>
        Запутанные детективы, масштабное историческое кино, вестерны, военные
        фильмы — выбор огромен.
      </li>
    </ul>
    <h2>Смотрите кино где угодно: на телефоне, планшете и Smart TV</h2>
    <p>
      Смотрите там, где вам удобно. Мы позаботились, чтобы наш онлайн-кинотеатр
      "летал" на любых устройствах. Вы можете смотреть фильмы на телефоне (будь
      то Android или iPhone), планшете (iPad) или вывести картинку на Smart TV.
      Комфорт просмотра — как на ПК.
    </p>
    <p>
      Дома, в дороге или в отпуске — любимое кино всегда с вами. Нужен только
      интернет. Больше не придется скачивать фильмы и забивать память
      устройства. Весь контент ждет вас для просмотра онлайн в любом браузере.
      Все работает быстро и без задержек.
    </p>
    <h2>Свежие новинки и отличный перевод</h2>
    <p>
      Хотите смотреть новинки первыми? Мы тоже. Наша команда отслеживает мировые
      премьеры и моментально добавляет свежие релизы. Как только появляется
      цифровой релиз, мы сразу обновляем качество до идеального (Blu-ray) и
      заливаем версии с хорошим переводом и профессиональной озвучкой. Наш сайт
      — это живой каталог, который пополняется каждый день.
    </p>
    <h2>Простой поиск и личные подборки</h2>
    <p>
      Найти нужное кино — проще простого. Мы сделали интуитивную навигацию и
      удобные фильтры по жанрам, годам и странам.
    </p>
    <p>
      А если не знаете, что выбрать, загляните в наши тематические подборки и
      топы. Мы постоянно собираем «топ фильмов», «лучшие сериалы», «топ
      мультфильмов» или «топ аниме». Система рекомендаций тоже не дремлет: она
      подкинет вам что-то новое и захватывающее, основываясь на том, что вы уже
      посмотрели.
    </p>
    <p>
      Так что заходите, начинайте смотреть кино онлайн бесплатно и без
      регистрации, выбирайте лучшие фильмы 2024 года и зовите друзей.
      Погружайтесь в мир кино вместе с нами!
    </p>
  </section>
</template>

<script setup>
import {
  computed,
  ref,
  onMounted,
  onBeforeUnmount,
  watch,
  nextTick,
} from "vue";
import MovieCard from "./MovieCard.vue";
import { useHomeFeed } from "../assets/useHomeFeed.js";
import {
  setMeta,
  setOg,
  setCanonical,
  setTwitter,
} from "../assets/seoUtils.js";

const feed = useHomeFeed();

const popularMovies = computed(() => feed.value.popular || []);

const moviesTab = ref("latest");
const seriesTab = ref("latest");
const cartoonsTab = ref("latest");
const animeTab = ref("latest");
const doramasTab = ref("latest");
const turkishTab = ref("latest");

const moviesPopular = ref([]);
const moviesRating = ref([]);
const seriesPopular = ref([]);
const seriesRating = ref([]);
const cartoonsPopular = ref([]);
const cartoonsRating = ref([]);
const animePopular = ref([]);
const animeRating = ref([]);
const doramasPopular = ref([]);
const doramasRating = ref([]);
const turkishPopular = ref([]);
const turkishRating = ref([]);

const moviesPending = ref(null);
const seriesPending = ref(null);
const cartoonsPending = ref(null);
const animePending = ref(null);
const doramasPending = ref(null);
const turkishPending = ref(null);

const displayedMovies = computed(() => {
  if (moviesTab.value === "popular") return moviesPopular.value;
  if (moviesTab.value === "rating") return moviesRating.value;
  return feed.value.sections?.filmy?.latest || [];
});
const displayedSeries = computed(() => {
  if (seriesTab.value === "popular") return seriesPopular.value;
  if (seriesTab.value === "rating") return seriesRating.value;
  return feed.value.sections?.serialy?.latest || [];
});
const displayedCartoons = computed(() => {
  if (cartoonsTab.value === "popular") return cartoonsPopular.value;
  if (cartoonsTab.value === "rating") return cartoonsRating.value;
  return feed.value.sections?.multfilmy?.latest || [];
});
const displayedAnime = computed(() => {
  if (animeTab.value === "popular") return animePopular.value;
  if (animeTab.value === "rating") return animeRating.value;
  return feed.value.sections?.anime?.latest || [];
});
const displayedDoramas = computed(() => {
  if (doramasTab.value === "popular") return doramasPopular.value;
  if (doramasTab.value === "rating") return doramasRating.value;
  return feed.value.sections?.doramas?.latest || [];
});
const displayedTurkish = computed(() => {
  if (turkishTab.value === "popular") return turkishPopular.value;
  if (turkishTab.value === "rating") return turkishRating.value;
  return feed.value.sections?.turkish?.latest || [];
});

// Lazy-mount flags
const seriesVisible = ref(false);
const cartoonsVisible = ref(false);
const animeVisible = ref(false);
const doramasVisible = ref(false);
const turkishVisible = ref(false);

// Sentinels
const seriesSentinel = ref(null);
const cartoonsSentinel = ref(null);
const animeSentinel = ref(null);
const doramasSentinel = ref(null);
const turkishSentinel = ref(null);

let lazyIO = null;

// Подгрузка вкладок из /api/category (поддерживает sort=rating|popularity и special)
async function fetchTab(listRef, name, sort, extra = {}) {
  try {
    const params = new URLSearchParams({
      name,
      page: "1",
      limit: "24",
      sort,
    });
    if (extra.special) params.set("special", String(extra.special));
    params.set("home", "1");
    const r = await fetch(`/api/category?${params.toString()}`);
    if (r.ok) {
      const j = await r.json();
      listRef.value = j.items || [];
    }
  } catch {}
}

const inFlight = new Map();

async function ensureTab(listRef, name, sort, extra = {}) {
  if (Array.isArray(listRef.value) && listRef.value.length) return;
  const key = JSON.stringify({
    name,
    sort,
    special: String(extra.special || ""),
  });
  if (inFlight.has(key)) return inFlight.get(key);
  const p = (async () => {
    await fetchTab(listRef, name, sort, extra);
  })();
  inFlight.set(
    key,
    p.finally(() => inFlight.delete(key))
  );
  return p;
}

async function requestMoviesTab(tab) {
  if (tab === moviesTab.value) return;
  if (tab === "popular") {
    if (!moviesPopular.value.length) {
      moviesPending.value = "popular";
      try {
        await ensureTab(moviesPopular, "filmy", "popularity");
        moviesTab.value = "popular";
      } finally {
        moviesPending.value = null;
      }
      return;
    }
    moviesTab.value = "popular";
  } else if (tab === "rating") {
    if (!moviesRating.value.length) {
      moviesPending.value = "rating";
      try {
        await ensureTab(moviesRating, "filmy", "rating");
        moviesTab.value = "rating";
      } finally {
        moviesPending.value = null;
      }
      return;
    }
    moviesTab.value = "rating";
  } else {
    moviesTab.value = "latest";
  }
}

async function requestSeriesTab(tab) {
  if (tab === seriesTab.value) return;
  if (tab === "popular") {
    if (!seriesPopular.value.length) {
      seriesPending.value = "popular";
      try {
        await ensureTab(seriesPopular, "serialy", "popularity");
        seriesTab.value = "popular";
      } finally {
        seriesPending.value = null;
      }
      return;
    }
    seriesTab.value = "popular";
  } else if (tab === "rating") {
    if (!seriesRating.value.length) {
      seriesPending.value = "rating";
      try {
        await ensureTab(seriesRating, "serialy", "rating");
        seriesTab.value = "rating";
      } finally {
        seriesPending.value = null;
      }
      return;
    }
    seriesTab.value = "rating";
  } else {
    seriesTab.value = "latest";
  }
}

async function requestCartoonsTab(tab) {
  if (tab === cartoonsTab.value) return;
  if (tab === "popular") {
    if (!cartoonsPopular.value.length) {
      cartoonsPending.value = "popular";
      try {
        await ensureTab(cartoonsPopular, "multfilmy", "popularity");
        cartoonsTab.value = "popular";
      } finally {
        cartoonsPending.value = null;
      }
      return;
    }
    cartoonsTab.value = "popular";
  } else if (tab === "rating") {
    if (!cartoonsRating.value.length) {
      cartoonsPending.value = "rating";
      try {
        await ensureTab(cartoonsRating, "multfilmy", "rating");
        cartoonsTab.value = "rating";
      } finally {
        cartoonsPending.value = null;
      }
      return;
    }
    cartoonsTab.value = "rating";
  } else {
    cartoonsTab.value = "latest";
  }
}

async function requestAnimeTab(tab) {
  if (tab === animeTab.value) return;
  if (tab === "popular") {
    if (!animePopular.value.length) {
      animePending.value = "popular";
      try {
        await ensureTab(animePopular, "anime", "popularity");
        animeTab.value = "popular";
      } finally {
        animePending.value = null;
      }
      return;
    }
    animeTab.value = "popular";
  } else if (tab === "rating") {
    if (!animeRating.value.length) {
      animePending.value = "rating";
      try {
        await ensureTab(animeRating, "anime", "rating");
        animeTab.value = "rating";
      } finally {
        animePending.value = null;
      }
      return;
    }
    animeTab.value = "rating";
  } else {
    animeTab.value = "latest";
  }
}

async function requestDoramasTab(tab) {
  if (tab === doramasTab.value) return;
  if (tab === "popular") {
    if (!doramasPopular.value.length) {
      doramasPending.value = "popular";
      try {
        await ensureTab(doramasPopular, "serialy", "popularity", {
          special: "doramas",
        });
        doramasTab.value = "popular";
      } finally {
        doramasPending.value = null;
      }
      return;
    }
    doramasTab.value = "popular";
  } else if (tab === "rating") {
    if (!doramasRating.value.length) {
      doramasPending.value = "rating";
      try {
        await ensureTab(doramasRating, "serialy", "rating", {
          special: "doramas",
        });
        doramasTab.value = "rating";
      } finally {
        doramasPending.value = null;
      }
      return;
    }
    doramasTab.value = "rating";
  } else {
    doramasTab.value = "latest";
  }
}

async function requestTurkishTab(tab) {
  if (tab === turkishTab.value) return;
  if (tab === "popular") {
    if (!turkishPopular.value.length) {
      turkishPending.value = "popular";
      try {
        await ensureTab(turkishPopular, "serialy", "popularity", {
          special: "turkish",
        });
        turkishTab.value = "popular";
      } finally {
        turkishPending.value = null;
      }
      return;
    }
    turkishTab.value = "popular";
  } else if (tab === "rating") {
    if (!turkishRating.value.length) {
      turkishPending.value = "rating";
      try {
        await ensureTab(turkishRating, "serialy", "rating", {
          special: "turkish",
        });
        turkishTab.value = "rating";
      } finally {
        turkishPending.value = null;
      }
      return;
    }
    turkishTab.value = "rating";
  } else {
    turkishTab.value = "latest";
  }
}

function prefetchAllTabs() {
  const tasks = [
    ensureTab(moviesPopular, "filmy", "popularity"),
    ensureTab(moviesRating, "filmy", "rating"),

    ensureTab(seriesPopular, "serialy", "popularity"),
    ensureTab(seriesRating, "serialy", "rating"),

    ensureTab(cartoonsPopular, "multfilmy", "popularity"),
    ensureTab(cartoonsRating, "multfilmy", "rating"),

    ensureTab(animePopular, "anime", "popularity"),
    ensureTab(animeRating, "anime", "rating"),

    ensureTab(doramasPopular, "serialy", "popularity", { special: "doramas" }),
    ensureTab(doramasRating, "serialy", "rating", { special: "doramas" }),

    ensureTab(turkishPopular, "serialy", "popularity", { special: "turkish" }),
    ensureTab(turkishRating, "serialy", "rating", { special: "turkish" }),
  ];
  return Promise.allSettled(tasks);
}

// Пример: по клику на таб меняйте computed на ref и подкачивайте
// (если нужно — могу доделать логику табов под вашу верстку)

onMounted(() => {
  if (typeof window === "undefined") return;

  // прелоад вкладок на LCP/idle
  const deferTabs = (fn) =>
    "requestIdleCallback" in window
      ? requestIdleCallback(fn, { timeout: 2500 })
      : setTimeout(fn, 1500);

  try {
    const po = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      if (entries && entries.length) {
        try {
          po.disconnect();
        } catch {}
        deferTabs(() => prefetchAllTabs());
      }
    });
    po.observe({ type: "largest-contentful-paint", buffered: true });
    setTimeout(() => {
      try {
        po.disconnect();
      } catch {}
      deferTabs(() => prefetchAllTabs());
    }, 1800);
  } catch {
    deferTabs(() => prefetchAllTabs());
  }

  const origin = window.location.origin;
  const logoAbs = `${origin}/assets/ProsmotrZone_site/images/NewLogo.webp`;
  const title =
    "ProsmotrZone - смотреть фильмы и сериалы в HD качестве онлайн бесплатно";
  const desc =
    "На ProsmotrZone вас ждут новые фильмы, сериалы и аниме онлайн. Смотрите премьеры 2025 года, классику, рейтинговые хиты и новинки. Здесь вы можете смотреть без регистрации бесплатно в HD (720p, 1080p) без лишней рекламы. Удобный поиск и фильтры по жанрам, актёрам, годам и другим параметрам. Можете смотреть с любого устройства в любое время дня.";
  document.title = title;
  setCanonical(origin + "/");
  setMeta("robots", "index,follow");
  setMeta("description", desc);
  setOg("og:url", origin + "/");
  setOg("og:type", "website");
  setOg("og:title", title);
  setOg("og:image", logoAbs);
  setOg("og:description", desc);
  setTwitter("twitter:card", "summary_large_image");
  setTwitter("twitter:title", title);
  setTwitter("twitter:description", desc);
  setTwitter("twitter:image", logoAbs);

  setTimeout(() => {
    const first = popularMovies?.value?.[0];
    if (first?.image) {
      const href = first.image.startsWith("http")
        ? first.image
        : `/${first.image}`;
      const l = document.createElement("link");
      l.rel = "preload";
      l.as = "image";
      l.href = href;
      document.head.appendChild(l);
    }
  }, 0);

  // IntersectionObserver for lazy sections
  const pairs = [
    [seriesSentinel, "series"],
    [cartoonsSentinel, "cartoons"],
    [animeSentinel, "anime"],
    [doramasSentinel, "doramas"],
    [turkishSentinel, "turkish"],
  ];
  const setVisible = (name) => {
    if (name === "series") seriesVisible.value = true;
    if (name === "cartoons") cartoonsVisible.value = true;
    if (name === "anime") animeVisible.value = true;
    if (name === "doramas") doramasVisible.value = true;
    if (name === "turkish") turkishVisible.value = true;
  };
  lazyIO = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const name =
            entry.target &&
            entry.target.dataset &&
            entry.target.dataset.section;
          if (name) setVisible(name);
          if (lazyIO) lazyIO.unobserve(entry.target);
        }
      });
    },
    { root: null, rootMargin: "200px 0px", threshold: 0.1 }
  );

  pairs.forEach(([r, name]) => {
    if (r && r.value) {
      r.value.dataset.section = name;
      lazyIO.observe(r.value);
    }
  });

  // УДАЛЕНО: вызовы несуществующей fetchCategorySorted(...)
  // Раньше здесь были отдельные вызовы — они ломали выполнение.
});

// Карусель функциональность (Owl Carousel)
const carousel = ref(null);

const ensureJquery = async () => {
  if (!window.jQuery && !window.$) {
    const s = document.createElement("script");
    s.src = "https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js";
    s.crossOrigin = "anonymous";
    await new Promise((resolve, reject) => {
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }
};

const ensureOwlPlugin = async () => {
  if (window.jQuery?.fn?.owlCarousel) return;
  await new Promise((resolve, reject) => {
    let s = document.querySelector('script[src="/vendor/owl-carousel.js"]');
    if (s && s.dataset.loaded === "1") return resolve();
    if (!s) {
      s = document.createElement("script");
      s.src = "/vendor/owl-carousel.js";
      s.defer = true;
      document.head.appendChild(s);
    }
    s.onload = () => {
      s.dataset.loaded = "1";
      resolve();
    };
    s.onerror = reject;
  });
};

const owlOptions = {
  loop: false,
  rewind: true,
  dots: false,
  autoplay: true,
  autoplayTimeout: 12000,
  nav: true,
  margin: 20,
  slideBy: 1,
  responsiveClass: true,
  autoRefresh: false,
  navText: [
    '<span class="fal fa-chevron-left"></span>',
    '<span class="fal fa-chevron-right"></span>',
  ],
  responsive: {
    0: { items: 2 },
    470: { items: 3 },
    590: { items: 3 },
    760: { items: 4 },
    950: { items: 5 },
    1220: { items: 6 },
  },
};

const initOwl = () => {
  if (!carousel.value || !window.jQuery?.fn?.owlCarousel) return;
  const $el = window.jQuery(carousel.value);
  if ($el.data("owl.carousel")) $el.trigger("refresh.owl.carousel");
  else $el.addClass("owl-carousel").owlCarousel(owlOptions);
};

const destroyOwl = () => {
  if (!carousel.value || !window.jQuery) return;
  const $el = window.jQuery(carousel.value);
  if ($el.data("owl.carousel")) {
    $el.trigger("destroy.owl.carousel");
    $el.removeClass("owl-carousel");
  }
};

onMounted(async () => {
  window.__OWL_NO_AUTO_INIT = true;
  await ensureJquery();
  await ensureOwlPlugin();
  await nextTick(); // дождаться рендера карточек
  initOwl();
  const { onActivated, onDeactivated } = await import("vue");
  onActivated(() => initOwl());
  onDeactivated(() => destroyOwl());
  window.__destroyHomeOwl = destroyOwl;
});

// если список популярных обновился — переинициализируем
watch(popularMovies, async (list) => {
  if (!list || !list.length) return;
  await nextTick();
  initOwl();
});

onBeforeUnmount(() => {
  if (window.__onRatingsUpdated) {
    window.removeEventListener("ratings-updated", window.__onRatingsUpdated);
    delete window.__onRatingsUpdated;
  }
  if (window.__destroyHomeOwl) {
    window.__destroyHomeOwl();
    delete window.__destroyHomeOwl;
  }
  if (lazyIO) {
    lazyIO.disconnect();
    lazyIO = null;
  }
});
</script>

<style scoped>
/* Owl Carousel будет использовать свои стили */
</style>
