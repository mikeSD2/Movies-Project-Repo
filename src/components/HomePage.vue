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
    <div class="section__header d-flex ai-center c-gap-20">
      <router-link
        to="/filmy"
        class="section__title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Фильмы</h2>
      </router-link>
      <div class="section__tabs d-flex c-gap-10">
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
    <div class="section__content grid-items">
      <MovieCard
        v-for="movie in displayedMovies"
        :key="movie.id"
        :movie="movie"
      />
    </div>
  </section>

  <!-- Секция сериалов -->
  <section class="sect">
    <div class="section__header d-flex ai-center c-gap-20">
      <router-link
        to="/serialy"
        class="section__title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Сериалы</h2>
      </router-link>
      <div class="section__tabs d-flex c-gap-10">
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
    <div class="section__content grid-items" v-if="seriesVisible">
      <MovieCard
        v-for="series in displayedSeries"
        :key="series.id"
        :movie="series"
      />
    </div>
  </section>

  <!-- Секция мультфильмов -->
  <section class="sect">
    <div class="section__header d-flex ai-center c-gap-20">
      <router-link
        to="/multfilmy"
        class="section__title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Мультфильмы</h2>
      </router-link>
      <div class="section__tabs d-flex c-gap-10">
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
    <ol class="section__content grid-items" v-if="cartoonsVisible">
      <MovieCard
        v-for="cartoon in displayedCartoons"
        :key="cartoon.id"
        :movie="cartoon"
      />
    </ol>
  </section>

  <!-- Секция аниме -->
  <section class="sect">
    <div class="section__header d-flex ai-center c-gap-20">
      <router-link
        to="/anime"
        class="section__title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Аниме</h2>
      </router-link>
      <div class="section__tabs d-flex c-gap-10">
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
    <div class="section__content grid-items" v-if="animeVisible">
      <MovieCard
        v-for="anime in displayedAnime"
        :key="anime.id"
        :movie="anime"
      />
    </div>
  </section>

  <!-- Секция дорам -->
  <section class="sect">
    <div class="section__header d-flex ai-center c-gap-20">
      <router-link
        to="/serialy?special=doramas"
        class="section__title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Дорамы</h2>
      </router-link>
      <div class="section__tabs d-flex c-gap-10">
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
    <div class="section__content grid-items" v-if="doramasVisible">
      <MovieCard
        v-for="dorama in displayedDoramas"
        :key="dorama.id"
        :movie="dorama"
      />
    </div>
  </section>

  <!-- Секция турецких сериалов -->
  <section class="sect">
    <div class="section__header d-flex ai-center c-gap-20">
      <router-link
        to="/serialy?special=turkish"
        class="section__title fal fa-chevron-right fa-pull-right btn"
      >
        <h2>Турецкие сериалы</h2>
      </router-link>
      <div class="section__tabs d-flex c-gap-10">
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
    <div class="section__content grid-items" v-if="turkishVisible">
      <MovieCard v-for="ts in displayedTurkish" :key="ts.id" :movie="ts" />
    </div>
  </section>

  <!-- Описание сайта -->
  <section class="descr">
    <h1>
      Ваш идеальный онлайн-кинотеатр: смотрите фильмы и сериалы бесплатно в
      лучшем качестве
    </h1>
    <p>
      После долгих рабочих или учебных будней каждому хочется отдохнуть и
      погрузиться в мир, далекий от повседневных забот. И что может быть лучше,
      чем смотреть любимые фильмы и сериалы? Мы создали для вас уникальный и
      максимально удобный онлайн-кинотеатр, где каждый найдет что-то для себя.
      Забудьте о необходимости искать сеансы в городских кинотеатрах, стоять в
      очередях за билетами или пытаться успеть на определенное время. Все эти
      хлопоты остались в прошлом, ведь теперь вы можете смотреть фильмы в
      отличном HD качестве онлайн прямо на нашем сайте, в любое удобное для вас
      время. Приглашаем вас окунуться в удивительный мир кинематографа,
      доступный круглосуточно и совершенно бесплатно!!!
    </p>
    <h2>Только лучшие фильмы и сериалы онлайн в гигантской коллекции</h2>
    <p>
      Наш главный приоритет — предоставить вам самый широкий выбор контента. В
      нашем ассортименте вы найдете всё: от вечных шедевров «Золотой эпохи»
      Голливуда и классического европейского кино до культовых французских
      комедий, динамичного азиатского кино и любимых многими поколений советских
      фильмов. Мы особенно гордимся нашей подборкой, которая включает
      современные хиты 2023, 2024 и 2025 годов.
    </p>
    <p>
      Мы собрали для вас внушительную подборку контента на любой вкус. Наша
      медиатека включает тысячи наименований в самых разных направлениях:
    </p>
    <ul>
      <li>Художественные и документальные фильмы</li>

      <li>Захватывающие боевики и триллеры</li>

      <li>Волшебные фэнтези и фантастика</li>

      <li>Трогательные драмы и мелодрамы</li>

      <li>Искрометные комедии и леденящие кровь ужасы</li>

      <li>Масштабные приключенческие и исторические ленты</li>

      <li>Запутанные детективы и классические вестерны</li>

      <li>
        Фильмы на военную тематику, сериалы о сыщиках и паранормальных явлениях.
      </li>
    </ul>
    <p>
      Вы всегда можете найти нужную киноленту, воспользовавшись категориями в
      меню сайта. Наша цель — удовлетворить запросы самой широкой аудитории,
      поэтому мы постоянно работаем над расширением коллекции.
    </p>
    <h2>Наслаждайтесь просмотром где угодно и как угодно</h2>
    <p>
      Радостная новость для наших зрителей: теперь наш онлайн-кинотеатр
      полностью адаптирован для мобильных устройств. Вы можете смотреть любимые
      фильмы и сериалы не только на компьютере, но и прямо со смартфона или
      планшета на iPhone, iPad и Android. Находитесь ли вы дома, в дороге или в
      путешествии в любой точке мира — ваша коллекция кино всегда с вами. Все,
      что вам нужно, — это доступ в интернет.
    </p>
    <p>
      Мы гарантируем, что все фильмы имеют высокое HD 1080p качество видео и
      звука, а многие новинки кино доступны даже в качестве 4K. Вам больше не
      обязательно скачивать тяжелые файлы и занимать место на диске — все можно
      смотреть в режиме онлайн. Наш сервис отлично работает на любом браузере,
      обеспечивая плавное и комфортное воспроизведение.
    </p>
    <h2>Всегда актуальные новинки и оперативные обновления</h2>
    <p>
      Мы тщательно следим за трендами в мировой киноиндустрии и стараемся
      своевременно добавлять на сайт актуальные новинки. Мы стремимся оперативно
      добавлять новинки практически сразу после их выхода в кинотеатрах. После
      официального цифрового релиза мы регулярно обновляем их качество до
      максимально возможного, включая версии с дисков DVD или Blu-ray. Наш сайт
      — это настоящее хранилище актуального контента, которое регулярно
      пополняется.
    </p>
    <p>
      Если вы затрудняетесь с выбором фильма на вечер или не можете найти
      конкретную ленту, смело обращайтесь в нашу службу поддержки. Мы всегда
      готовы проконсультировать вас по уже вышедшим фильмам 2024 года, которые
      можно смотреть онлайн, и постараемся добавить необходимый вам контент.
      Ваше мнение очень важно для нас, и мы всегда учитываем требования нашей
      аудитории для развития ресурса.
    </p>
    <h2>Удобная навигация и персональные подборки</h2>
    <p>
      Мы позаботились о том, чтобы вы легко находили интересующий вас контент.
      На сайте реализованы удобные фильтры по жанрам, годам выпуска и странам,
      которые помогут быстро отсортировать фильмы и сериалы. Кроме того, мы
      регулярно составляем тематические подборки и топы, такие как «топ
      фильмов», «топ сериалов», «топ мультфильмов» и «топ аниме», чтобы вы
      всегда были в курсе лучших новинок и признанных шедевров кинематографа.
      Наша система рекомендаций поможет вам открыть для себя новые захватывающие
      картины на основе ваших предпочтений.
    </p>
    <p>
      Приглашаем вас смотреть фильмы онлайн, выбирать лучшие ленты, приглашать
      друзей и делиться впечатлениями. Присоединяйтесь к миллионам довольных
      зрителей и погружайтесь в увлекательный мир кино вместе с нами — в любое
      время, сколько угодно и абсолютно бесплатно!
    </p>
  </section>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from "vue";
import MovieCard from "./MovieCard.vue";
import { useHomeFeed } from "../assets/useHomeFeed.js";
import { setMeta, setOg, setCanonical } from "../assets/seoUtils.js";

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
      sort
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
  const key = JSON.stringify({ name, sort, special: String(extra.special || '') });
  if (inFlight.has(key)) return inFlight.get(key);
  const p = (async () => {
    await fetchTab(listRef, name, sort, extra);
  })();
  inFlight.set(key, p.finally(() => inFlight.delete(key)));
  return p;
}

async function requestMoviesTab(tab) {
  if (tab === moviesTab.value) return;
  if (tab === 'popular') {
    if (!moviesPopular.value.length) {
      moviesPending.value = 'popular';
      try {
        await ensureTab(moviesPopular, 'filmy', 'popularity');
        moviesTab.value = 'popular';
      } finally {
        moviesPending.value = null;
      }
      return;
    }
    moviesTab.value = 'popular';
  } else if (tab === 'rating') {
    if (!moviesRating.value.length) {
      moviesPending.value = 'rating';
      try {
        await ensureTab(moviesRating, 'filmy', 'rating');
        moviesTab.value = 'rating';
      } finally {
        moviesPending.value = null;
      }
      return;
    }
    moviesTab.value = 'rating';
  } else {
    moviesTab.value = 'latest';
  }
}

async function requestSeriesTab(tab) {
  if (tab === seriesTab.value) return;
  if (tab === 'popular') {
    if (!seriesPopular.value.length) {
      seriesPending.value = 'popular';
      try {
        await ensureTab(seriesPopular, 'serialy', 'popularity');
        seriesTab.value = 'popular';
      } finally {
        seriesPending.value = null;
      }
      return;
    }
    seriesTab.value = 'popular';
  } else if (tab === 'rating') {
    if (!seriesRating.value.length) {
      seriesPending.value = 'rating';
      try {
        await ensureTab(seriesRating, 'serialy', 'rating');
        seriesTab.value = 'rating';
      } finally {
        seriesPending.value = null;
      }
      return;
    }
    seriesTab.value = 'rating';
  } else {
    seriesTab.value = 'latest';
  }
}

async function requestCartoonsTab(tab) {
  if (tab === cartoonsTab.value) return;
  if (tab === 'popular') {
    if (!cartoonsPopular.value.length) {
      cartoonsPending.value = 'popular';
      try {
        await ensureTab(cartoonsPopular, 'multfilmy', 'popularity');
        cartoonsTab.value = 'popular';
      } finally {
        cartoonsPending.value = null;
      }
      return;
    }
    cartoonsTab.value = 'popular';
  } else if (tab === 'rating') {
    if (!cartoonsRating.value.length) {
      cartoonsPending.value = 'rating';
      try {
        await ensureTab(cartoonsRating, 'multfilmy', 'rating');
        cartoonsTab.value = 'rating';
      } finally {
        cartoonsPending.value = null;
      }
      return;
    }
    cartoonsTab.value = 'rating';
  } else {
    cartoonsTab.value = 'latest';
  }
}

async function requestAnimeTab(tab) {
  if (tab === animeTab.value) return;
  if (tab === 'popular') {
    if (!animePopular.value.length) {
      animePending.value = 'popular';
      try {
        await ensureTab(animePopular, 'anime', 'popularity');
        animeTab.value = 'popular';
      } finally {
        animePending.value = null;
      }
      return;
    }
    animeTab.value = 'popular';
  } else if (tab === 'rating') {
    if (!animeRating.value.length) {
      animePending.value = 'rating';
      try {
        await ensureTab(animeRating, 'anime', 'rating');
        animeTab.value = 'rating';
      } finally {
        animePending.value = null;
      }
      return;
    }
    animeTab.value = 'rating';
  } else {
    animeTab.value = 'latest';
  }
}

async function requestDoramasTab(tab) {
  if (tab === doramasTab.value) return;
  if (tab === 'popular') {
    if (!doramasPopular.value.length) {
      doramasPending.value = 'popular';
      try {
        await ensureTab(doramasPopular, 'serialy', 'popularity', { special: 'doramas' });
        doramasTab.value = 'popular';
      } finally {
        doramasPending.value = null;
      }
      return;
    }
    doramasTab.value = 'popular';
  } else if (tab === 'rating') {
    if (!doramasRating.value.length) {
      doramasPending.value = 'rating';
      try {
        await ensureTab(doramasRating, 'serialy', 'rating', { special: 'doramas' });
        doramasTab.value = 'rating';
      } finally {
        doramasPending.value = null;
      }
      return;
    }
    doramasTab.value = 'rating';
  } else {
    doramasTab.value = 'latest';
  }
}

async function requestTurkishTab(tab) {
  if (tab === turkishTab.value) return;
  if (tab === 'popular') {
    if (!turkishPopular.value.length) {
      turkishPending.value = 'popular';
      try {
        await ensureTab(turkishPopular, 'serialy', 'popularity', { special: 'turkish' });
        turkishTab.value = 'popular';
      } finally {
        turkishPending.value = null;
      }
      return;
    }
    turkishTab.value = 'popular';
  } else if (tab === 'rating') {
    if (!turkishRating.value.length) {
      turkishPending.value = 'rating';
      try {
        await ensureTab(turkishRating, 'serialy', 'rating', { special: 'turkish' });
        turkishTab.value = 'rating';
      } finally {
        turkishPending.value = null;
      }
      return;
    }
    turkishTab.value = 'rating';
  } else {
    turkishTab.value = 'latest';
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
    ensureTab(turkishRating, "serialy", "rating", { special: "turkish" })
  ];
  return Promise.allSettled(tasks);
}


// Пример: по клику на таб меняйте computed на ref и подкачивайте
// (если нужно — могу доделать логику табов под вашу верстку)

onMounted(() => {
  if (typeof window === 'undefined') return;

  // стартуем прелоад всех вкладок сразу (без ожидания остальных инициализаций)
  prefetchAllTabs();

  const origin = window.location.origin;
  const title = "LordFilm — фильмы, сериалы и аниме онлайн";
  const desc = "Смотрите фильмы, сериалы и аниме онлайн в HD. Без регистрации — LordFilm.";
  document.title = title;
  setMeta("description", desc);
  setOg("og:type", "website");
  setOg("og:title", title);
  setOg("og:description", desc);
  setOg("og:url", origin + "/");
  setCanonical(origin + "/");

  setTimeout(() => {
    const first = popularMovies?.value?.[0];
    if (first?.image) {
      const href = first.image.startsWith('http') ? first.image : `/${first.image}`;
      const l = document.createElement('link');
      l.rel = 'preload';
      l.as = 'image';
      l.href = href;
      document.head.appendChild(l);
    }
  }, 0);

  // IntersectionObserver for lazy sections
  const pairs = [
    [seriesSentinel, 'series'],
    [cartoonsSentinel, 'cartoons'],
    [animeSentinel, 'anime'],
    [doramasSentinel, 'doramas'],
    [turkishSentinel, 'turkish']
  ];
  const setVisible = (name) => {
    if (name === 'series') seriesVisible.value = true;
    if (name === 'cartoons') cartoonsVisible.value = true;
    if (name === 'anime') animeVisible.value = true;
    if (name === 'doramas') doramasVisible.value = true;
    if (name === 'turkish') turkishVisible.value = true;
  };
  lazyIO = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const name = entry.target && entry.target.dataset && entry.target.dataset.section;
        if (name) setVisible(name);
        if (lazyIO) lazyIO.unobserve(entry.target);
      }
    });
  }, { root: null, rootMargin: '200px 0px', threshold: 0.1 });

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

onMounted(async () => {
  // jQuery уже подгружается глобально в <head>; фолбэк на случай отсутствия
  if (!window.jQuery && !window.$) {
    const { default: $ } = await import("jquery");
    window.jQuery = $;
    window.$ = $;
  }

  // Флаг защиты от авто‑инициализации (на случай SPA-навигации)
  window.__OWL_NO_AUTO_INIT = true;

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
    if (!carousel.value || !window.jQuery) return;
    const $el = window.jQuery(carousel.value);
    if ($el.data("owl.carousel")) {
      $el.trigger("refresh.owl.carousel");
    } else {
      $el.addClass("owl-carousel").owlCarousel(owlOptions);
    }
  };

  const destroyOwl = () => {
    if (!carousel.value || !window.jQuery) return;
    const $el = window.jQuery(carousel.value);
    if ($el.data("owl.carousel")) {
      $el.trigger("destroy.owl.carousel");
      $el.removeClass("owl-carousel");
    }
  };

  // Скрипт плагина уже добавлен в <head> — просто инициализируем
  if (document.querySelector('script[src="/vendor/owl-carousel.js"]')) {
    initOwl();
  }

  const { onActivated, onDeactivated } = await import("vue");
  onActivated(() => initOwl());
  onDeactivated(() => destroyOwl());
  window.__destroyHomeOwl = destroyOwl;
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
