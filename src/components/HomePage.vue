<template>
  <!-- Карусель популярных -->
  <div class="carou">
    <div class="carou__caption">Популярные за месяц</div>
    <div class="unique-kicker" style="font-size:12px;opacity:.75;margin:6px 0 0;">
      Мини-примечание: карусель формируется автоматически по популярности за последние 30 дней.
    </div>
    <div class="carou__content karuselMy-grid" id="top-carou" ref="carousel">
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
    <div class="section--header d-flex ai-center c-gap-20">
      <router-link
        to="/filmy"
        class="section--title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Фильмы</h2>
      </router-link>
      <div class="section--tabs d-flex c-gap-10">
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
    <!-- homepage:movies-tabs seed:2a -->
    <div class="section--content items-in-grid">
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
    <div class="section--header d-flex ai-center c-gap-20">
      <router-link
        to="/serialy"
        class="section--title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Сериалы</h2>
      </router-link>
      <div class="section--tabs d-flex c-gap-10">
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
    <div class="section--content items-in-grid" v-if="seriesVisible">
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
    <div class="section--header d-flex ai-center c-gap-20">
      <router-link
        to="/multfilmy"
        class="section--title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Мультфильмы</h2>
      </router-link>
      <div class="section--tabs d-flex c-gap-10">
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
    <div class="section--content items-in-grid" v-if="cartoonsVisible">
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
    <div class="section--header d-flex ai-center c-gap-20">
      <router-link
        to="/anime"
        class="section--title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Аниме</h2>
      </router-link>
      <div class="section--tabs d-flex c-gap-10">
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
    <!-- homepage:anime-note seed:9f -->
    <div ref="animeSentinel" class="lazy-sentinel" aria-hidden="true"></div>
    <div class="section--content items-in-grid" v-if="animeVisible">
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
    <div class="section--header d-flex ai-center c-gap-20">
      <router-link
        to="/serialy?special=doramas"
        class="section--title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Дорамы</h2>
      </router-link>
      <div class="section--tabs d-flex c-gap-10">
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
    <div class="section--content items-in-grid" v-if="doramasVisible">
      <MovieCard
        v-for="dorama in displayedDoramas"
        :key="dorama.id"
        :movie="dorama"
      />
    </div>
  </section> -->

  <!-- Секция турецких сериалов -->
  <!-- <section class="sect">
    <div class="section--header d-flex ai-center c-gap-20">
      <router-link
        to="/serialy?special=turkish"
        class="section--title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Турецкие сериалы</h2>
      </router-link>
      <div class="section--tabs d-flex c-gap-10">
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
    <div class="section--content items-in-grid" v-if="turkishVisible">
      <MovieCard v-for="ts in displayedTurkish" :key="ts.id" :movie="ts" />
    </div>
  </section> -->

  <!-- Описание сайта -->
  <section class="descr">
    <h1>
      Лордфилм — ваш онлайн-кинотеатр: смотрите фильмы и сериалы бесплатно в
      хорошем качестве
    </h1>

    <p>
      Устали после долгого дня? Лучший способ перезагрузиться — погрузиться в
      другую реальность. Наш <strong>онлайн-кинотеатр</strong> создан именно для
      этого. Мы предлагаем вам уровень комфорта и ассортимент, достойный
      <strong>Лордфилм</strong>, — это ваш личный портал в мир тысяч
      кинопроизведений, где можно
      <strong>смотреть фильмы онлайн бесплатно и без регистрации</strong>.
    </p>

    <h2>Кинозал, который всегда с вами</h2>
    <p>
      Забудьте о привязке к расписанию сеансов. Здесь вы сами управляете
      временем. Включайте <strong>фильмы онлайн</strong> тогда, когда удобно
      именно вам, и наслаждайтесь просмотром
      <strong>в хорошем качестве</strong>.
    </p>

    <ul>
      <li>
        <strong>Картинка:</strong> Вас ждет кристально чистое изображение
        <strong>HD 1080p</strong> (или <strong>720p</strong> для экономии
        трафика).
      </li>
      <li>
        <strong>Технологии:</strong> Многие <strong>новинки кино</strong> уже
        доступны в формате <strong>4K</strong>.
      </li>
      <li>
        <strong>Звук:</strong> Чистый звук, <strong>русская озвучка</strong> и
        профессиональный дубляж обеспечат полное погружение.
      </li>
    </ul>

    <p>
      Наш сервис работает по стандартам качества <strong>lordfilms</strong>,
      предлагая мгновенную загрузку и стабильный плеер.
    </p>

    <h2>Глобальная коллекция: от классики до хитов 2024 и 2025</h2>
    <p>
      Мы гордимся нашей библиотекой, которая постоянно растет. В каталоге
      собрано всё: культовые <strong>зарубежные фильмы</strong>, душевные
      отечественные ленты и <strong>лучшие фильмы и сериалы</strong> всех
      времен.
    </p>
    <p>Мы держим руку на пульсе индустрии, чтобы вы могли смотреть:</p>
    <ul>
      <li>
        Самые громкие <strong>новинки кино 2023</strong> и
        <strong>2024</strong> годов.
      </li>
      <li>
        Эксклюзивные премьеры и ожидаемые блокбастеры
        <strong>2025 года</strong>.
      </li>
      <li>Популярные <strong>мультфильмы</strong> для детей и взрослых.</li>
      <li>Захватывающее <strong>аниме</strong> разных жанров.</li>
    </ul>

    <p><strong>Навигация по жанрам удовлетворит любой вкус:</strong></p>
    <ul>
      <li>
        Любите адреналин? Включайте <strong>боевики</strong> и
        <strong>триллеры</strong>, от которых захватывает дух.
      </li>
      <li>
        Хотите эмоций? Для вас глубокие <strong>драмы</strong> и трогательные
        <strong>мелодрамы</strong>.
      </li>
      <li>
        Нужно расслабиться? Легкие <strong>комедии</strong> поднимут настроение,
        а <strong>ужасы</strong> пощекочут нервы.
      </li>
      <li>
        Мечтаете о других мирах? Разделы <strong>фантастики</strong> и
        <strong>фэнтези</strong> открыты для вас.
      </li>
      <li>
        Также в наличии: запутанные <strong>детективы</strong>, эпическое
        <strong>историческое кино</strong>, суровые <strong>вестерны</strong> и
        <strong>военные фильмы</strong>.
      </li>
    </ul>

    <h2>Смотрите кино где угодно: Смарт ТВ, телефон или планшет</h2>
    <p>
      Наш сайт оптимизирован так, чтобы работать идеально на любом устройстве,
      как и привычный многим <strong>lordfilm</strong>.
    </p>

    <ul>
      <li>
        <strong>На телефоне:</strong> Комфортный просмотр на
        <strong>Android</strong> и <strong>iPhone</strong>.
      </li>
      <li>
        <strong>На планшете:</strong> Идеальная адаптация для
        <strong>iPad</strong> и других устройств.
      </li>
      <li>
        <strong>На большом экране:</strong> Выводите картинку на
        <strong>Smart TV</strong> и наслаждайтесь домашним кинотеатром.
      </li>
    </ul>

    <p>
      Вам больше не нужно скачивать файлы и занимать память гаджетов. Достаточно
      доступа в интернет, чтобы <strong>смотреть кино онлайн</strong> в любом
      браузере — дома, в дороге или в отпуске.
    </p>

    <h2>Свежие релизы, передовая озвучка и удобный поиск</h2>
    <p>
      Как только в сети появляется цифровой релиз (WEB-DL или
      <strong>Blu-ray</strong>), он моментально оказывается у нас. Мы оперативно
      добавляем версии с <strong>хорошим переводом</strong> и
      <strong>профессиональной озвучкой</strong>.
    </p>
    <p>
      Найти, что посмотреть вечером, проще простого. Используйте умные фильтры
      по годам, странам и жанрам. А если глаза разбегаются — доверьтесь нашим
      подборкам:
    </p>

    <ul>
      <li><strong>Топ фильмов</strong> по рейтингу зрителей.</li>
      <li><strong>Лучшие сериалы</strong> сезона.</li>
      <li><strong>Топ мультфильмов</strong> и <strong>топ аниме</strong>.</li>
    </ul>

    <p>
      Система рекомендаций, работающая не хуже, чем на
      <strong>Лордфилм</strong>, предложит вам контент на основе ваших
      предпочтений.
    </p>

    <p>
      <strong>Заходите прямо сейчас!</strong> Начинайте
      <strong>смотреть кино онлайн бесплатно</strong>, оцените
      <strong>лучшие фильмы 2024 года</strong> и зовите друзей. Приятного
      просмотра!
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
  const logoAbs = `${origin}/assets/NewLord_site/images/logo.svg`;
  const title =
    "Lordfilm — смотреть новинки фильмов 2025 и сериалы онлайн бесплатно в HD 1080";
  const desc =
    "Ищете, где посмотреть кино? На Лордфилм вас ждут свежие хиты 2025, популярные сериалы и мультфильмы в хорошем качестве. Удобный плеер позволяет смотреть онлайн без регистрации и тормозов в Full HD 720 или 1080. Находите контент по жанрам и актерам за пару кликов. Доступно круглосуточно на любом устройстве бесплатно.";
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
