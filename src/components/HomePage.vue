<template>
  <!-- Карусель популярных -->
  <div class="carou">
    <div class="carou__caption">Популярные за месяц</div>
    <div class="carou__content carousel-grid" id="top-carou" ref="carousel">
      <MovieCard
        v-for="movie in popularMovies"
        :key="movie.id"
        :movie="movie"
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
          @click="moviesTab = 'popular'"
        >
          Популярные
        </button>
        <button
          :class="{ 'is-active': moviesTab === 'rating' }"
          @click="moviesTab = 'rating'"
        >
          По рейтингу
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
          @click="seriesTab = 'popular'"
        >
          Популярные
        </button>
        <button
          :class="{ 'is-active': seriesTab === 'rating' }"
          @click="seriesTab = 'rating'"
        >
          По рейтингу
        </button>
      </div>
    </div>
    <div class="section__content grid-items">
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
          @click="cartoonsTab = 'popular'"
        >
          Популярные
        </button>
        <button
          :class="{ 'is-active': cartoonsTab === 'rating' }"
          @click="cartoonsTab = 'rating'"
        >
          По рейтингу
        </button>
      </div>
    </div>
    <ol class="section__content grid-items">
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
          @click="animeTab = 'popular'"
        >
          Популярные
        </button>
        <button
          :class="{ 'is-active': animeTab === 'rating' }"
          @click="animeTab = 'rating'"
        >
          По рейтингу
        </button>
      </div>
    </div>
    <div class="section__content grid-items">
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
          @click="doramasTab = 'popular'"
        >
          Популярные
        </button>
        <button
          :class="{ 'is-active': doramasTab === 'rating' }"
          @click="doramasTab = 'rating'"
        >
          По рейтингу
        </button>
      </div>
    </div>
    <div class="section__content grid-items">
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
          @click="turkishTab = 'popular'"
        >
          Популярные
        </button>
        <button
          :class="{ 'is-active': turkishTab === 'rating' }"
          @click="turkishTab = 'rating'"
        >
          По рейтингу
        </button>
      </div>
    </div>
    <div class="section__content grid-items">
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
      доступный круглосуточно и совершенно бесплатно!
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
import moviesData from "../../movies-data.json";

function upsertTag(selector, create) {
  let el = document.head.querySelector(selector);
  if (!el) {
    el = create();
    document.head.appendChild(el);
  }
  return el;
}
function setMeta(name, content) {
  if (!content) return;
  upsertTag(`meta[name="${name}"]`, () => {
    const m = document.createElement("meta");
    m.setAttribute("name", name);
    return m;
  }).setAttribute("content", content);
}
function setOg(property, content) {
  if (!content) return;
  upsertTag(`meta[property="${property}"]`, () => {
    const m = document.createElement("meta");
    m.setAttribute("property", property);
    return m;
  }).setAttribute("content", content);
}
function setCanonical(url) {
  upsertTag('link[rel="canonical"]', () => {
    const l = document.createElement("link");
    l.setAttribute("rel", "canonical");
    return l;
  }).setAttribute("href", url);
}

onMounted(() => {
  const origin = window.location.origin;
  const title = "LordFilm — фильмы, сериалы и аниме онлайн";
  const desc =
    "Смотрите фильмы, сериалы и аниме онлайн в HD. Без регистрации — LordFilm.";
  document.title = title;
  setMeta("description", desc);
  setOg("og:type", "website");
  setOg("og:title", title);
  setOg("og:description", desc);
  setOg("og:url", origin + "/");
  setCanonical(origin + "/");
});

const monthMap = {
  января: "01",
  февраля: "02",
  марта: "03",
  апреля: "04",
  мая: "05",
  июня: "06",
  июля: "07",
  августа: "08",
  сентября: "09",
  октября: "10",
  ноября: "11",
  декабря: "12",
};

const parseRussianDate = (dateString) => {
  if (!dateString) return null;
  const parts = dateString.split(" ");
  if (parts.length < 3) return null;

  const day = parts[0].padStart(2, "0");
  const month = monthMap[parts[1]];
  const year = parts[2];

  if (!month) return null;

  const isoDate = `${year}-${month}-${day}`;
  const date = new Date(isoDate);
  return isNaN(date.getTime()) ? null : date;
};

// Получаем данные по категориям
const allMovies = moviesData.movies.filter((m) => {
  if (m.id === "index") return false;

  // 1. Фильтр по дате премьеры
  const premiereDate = parseRussianDate(m.premiere);
  if (!premiereDate || premiereDate > new Date()) {
    return false;
  }

  // 2. Фильтр по наличию рейтинга IMDb
  if (!m.imdbRating) {
    return false;
  }

  // 3. Фильтр по стране
  if (m.country) {
    const country = m.country.toLowerCase();
    if (country.includes("индия") || country.includes("пакистан")) {
      return false;
    }
  }

  return true;
});

// Состояние активных табов
const moviesTab = ref("latest");
const seriesTab = ref("latest");
const cartoonsTab = ref("latest");
const animeTab = ref("latest");
const doramasTab = ref("latest");
const turkishTab = ref("latest");

// Кэш серверных лайков/дизлайков и загрузка
const ratingsData = ref({});

async function fetchRatings() {
  try {
    const response = await fetch("/api/all-ratings");
    if (response.ok) ratingsData.value = await response.json();
  } catch (e) {
    console.error("Error fetching ratings:", e);
  }
}

// Популярные фильмы (топ-рейтинг)
const popularMovies = computed(() => {
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

  const recentMovies = allMovies.filter((movie) => {
    const premiereDate = parseRussianDate(movie.premiere);
    return premiereDate && premiereDate >= thirtyDaysAgo;
  });

  // Сортировка по TMDb popularity
  let popularRecentMovies = [];
  if (recentMovies.length > 0) {
    popularRecentMovies = recentMovies.sort(
      (a, b) => (b.popularity || 0) - (a.popularity || 0)
    );
  }

  const desiredCount = 12;

  if (popularRecentMovies.length >= desiredCount) {
    return popularRecentMovies.slice(0, desiredCount);
  }

  // Дополнить самыми популярными за всё время по popularity
  const recentMovieIds = new Set(popularRecentMovies.map((m) => m.id));

  const allTimePopular = allMovies.sort(
    (a, b) => (b.popularity || 0) - (a.popularity || 0)
  );

  const additionalMovies = allTimePopular
    .filter((movie) => !recentMovieIds.has(movie.id))
    .slice(0, desiredCount - popularRecentMovies.length);

  return [...popularRecentMovies, ...additionalMovies];
});

// Логика для отображения контента в секциях
const getSortedMovies = (category, sortBy) => {
  const movies = allMovies.filter((movie) => movie.category === category);

  if (sortBy === "latest" || sortBy === "popular") {
    const oneYearAgo = new Date();
    oneYearAgo.setDate(oneYearAgo.getDate() - 365);
    const recentMovies = movies.filter((movie) => {
      const premiereDate = parseRussianDate(movie.premiere);
      return premiereDate && premiereDate >= oneYearAgo;
    });

    if (sortBy === "popular") {
      // Популярность по TMDb popularity
      return [...recentMovies]
        .sort((a, b) => (b.popularity || 0) - (a.popularity || 0))
        .slice(0, 24);
    }
    // latest
    return [...recentMovies]
      .sort(
        (a, b) =>
          (parseRussianDate(b.premiere)?.getTime() || 0) -
          (parseRussianDate(a.premiere)?.getTime() || 0)
      )
      .slice(0, 24);
  }

  // rating
  const twoYearsAgo = new Date();
  twoYearsAgo.setDate(twoYearsAgo.getDate() - 365 * 2);
  const moviesForRating = movies.filter((movie) => {
    const premiereDate = parseRussianDate(movie.premiere);
    return premiereDate && premiereDate >= twoYearsAgo;
  });

  return [...moviesForRating]
    .sort((a, b) => {
      const ratingA = Math.max(a.imdbRating || 0, a.kpRating || 0);
      const ratingB = Math.max(b.imdbRating || 0, b.kpRating || 0);
      return ratingB - ratingA;
    })
    .slice(0, 24);
};

// Универсальная сортировка произвольного списка
const getSortedFromList = (list, sortBy) => {
  if (sortBy === "latest" || sortBy === "popular") {
    const oneYearAgo = new Date();
    oneYearAgo.setDate(oneYearAgo.getDate() - 365);
    const recentMovies = list.filter((movie) => {
      const premiereDate = parseRussianDate(movie.premiere);
      return premiereDate && premiereDate >= oneYearAgo;
    });

    if (sortBy === "popular") {
      // Популярность по TMDb popularity
      return [...recentMovies]
        .sort((a, b) => (b.popularity || 0) - (a.popularity || 0))
        .slice(0, 24);
    }
    // latest
    return [...recentMovies]
      .sort(
        (a, b) =>
          (parseRussianDate(b.premiere)?.getTime() || 0) -
          (parseRussianDate(a.premiere)?.getTime() || 0)
      )
      .slice(0, 24);
  }

  // rating
  const twoYearsAgo = new Date();
  twoYearsAgo.setDate(twoYearsAgo.getDate() - 365 * 2);
  const moviesForRating = list.filter((movie) => {
    const premiereDate = parseRussianDate(movie.premiere);
    return premiereDate && premiereDate >= twoYearsAgo;
  });

  return [...moviesForRating]
    .sort((a, b) => {
      const ratingA = Math.max(a.imdbRating || 0, a.kpRating || 0);
      const ratingB = Math.max(b.imdbRating || 0, b.kpRating || 0);
      return ratingB - ratingA;
    })
    .slice(0, 24);
};

const displayedMovies = computed(() =>
  getSortedMovies("filmy", moviesTab.value)
);
const displayedSeries = computed(() =>
  getSortedMovies("serialy", seriesTab.value)
);
const displayedCartoons = computed(() =>
  getSortedMovies("multfilmy", cartoonsTab.value)
);
const displayedAnime = computed(() => getSortedMovies("anime", animeTab.value));

// Фильтры для дорам и турецких сериалов
const asianKeywords = [
  "южная корея",
  "корея",
  "северная корея",
  "япония",
  "китай",
  "тайвань",
  "гонконг",
  "таиланд",
  "индонезия",
  "малайзия",
  "вьетнам",
  "сингапур",
  "филиппины",
];
const isAsianCountry = (countryStr) => {
  if (!countryStr) return false;
  const s = String(countryStr).toLowerCase();
  return asianKeywords.some((k) => s.includes(k));
};
const isTurkish = (countryStr) => /турция/i.test(countryStr || "");

const doramasList = computed(() =>
  allMovies.filter(
    (m) =>
      m.category === "serialy" &&
      isAsianCountry(m.country) &&
      !isTurkish(m.country)
  )
);
const turkishList = computed(() =>
  allMovies.filter((m) => m.category === "serialy" && isTurkish(m.country))
);

const displayedDoramas = computed(() =>
  getSortedFromList(doramasList.value, doramasTab.value)
);
const displayedTurkish = computed(() =>
  getSortedFromList(turkishList.value, turkishTab.value)
);

// Последние фильмы
const latestMovies = computed(() => {
  return allMovies
    .filter((movie) => movie.category === "filmy")
    .sort((a, b) => b.year - a.year)
    .slice(0, 24);
});

// Последние сериалы
const latestSeries = computed(() => {
  return allMovies
    .filter((movie) => movie.category === "serialy")
    .sort((a, b) => b.year - a.year)
    .slice(0, 24);
});

// Последние мультфильмы
const latestCartoons = computed(() => {
  return allMovies
    .filter((movie) => movie.category === "multfilmy")
    .sort((a, b) => b.year - a.year)
    .slice(0, 24);
});

// Последние аниме
const latestAnime = computed(() => {
  return allMovies
    .filter((movie) => movie.category === "anime")
    .sort((a, b) => b.year - a.year)
    .slice(0, 24);
});

// Карусель функциональность (Owl Carousel)
const carousel = ref(null);

onMounted(async () => {
  await fetchRatings();

  // 1) jQuery
  const { default: $ } = await import("jquery");
  window.jQuery = $;
  window.$ = $;

  // 2) Флаг для отключения авто-init в плагине
  window.__OWL_NO_AUTO_INIT = true;

  // Опции карусели
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

  // 3) Вставляем скрипт один раз
  const src = "/vendor/owl-carousel.js";
  if (!document.querySelector(`script[src="${src}"]`)) {
    const s = document.createElement("script");
    s.src = src;
    s.onload = () => initOwl();
    document.head.appendChild(s);
  } else {
    // Скрипт уже загружен — init/refresh (SPA возврат на главную)
    initOwl();
  }

  // Инициализация при возврате по «назад»
  const { onActivated, onDeactivated } = await import("vue");
  onActivated(() => initOwl());
  onDeactivated(() => destroyOwl());

  // Сделаем доступным для onBeforeUnmount
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
});
</script>

<style scoped>
/* Owl Carousel будет использовать свои стили */
</style>
