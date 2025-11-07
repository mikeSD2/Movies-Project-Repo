require("dotenv").config({ path: "./config.env" });
const express = require("express");
const fs = require("fs").promises;
const fsSync = require("fs");
const path = require("path");
const cors = require("cors");
const axios = require("axios");
const Critters = require("critters");
const compression = require("compression");

async function createServerApp() {
  const app = express();
  app.use((req, res, next) => {
    if (process.env.BLOCK_INDEXING === "true") {
      res.set("X-Robots-Tag", "noindex, nofollow, noarchive");
    }
    next();
  });
  const PORT = process.env.SERVER_PORT || 3000;
  const RAW_BASE_URL =
    process.env.PUBLIC_BASE_URL || `http://localhost:${PORT}`;
  const BASE_URL = RAW_BASE_URL.replace(/\/+$/, "");
  const isProduction = process.env.NODE_ENV === "production";

  // SSR setup
  let vite;
  let template;
  let render;

  // Статика ДОЛЖНА идти раньше Vite в dev
  const DEV_STATIC = [
    ["/assets", path.resolve("assets")],
    ["/uploads", path.resolve("uploads")],
  ];

  if (!isProduction) {
    // Development - Vite middleware
    // Статика перед Vite, чтобы Vite не ловил /uploads и /assets
    for (const [route, dir] of DEV_STATIC) {
      app.use(route, express.static(dir, { maxAge: "0" }));
    }

    const { createServer } = await import("vite");
    vite = await createServer({
      server: { middlewareMode: true },
      appType: "custom",
    });
    app.use(vite.middlewares);
  } else {
    // Production - читаем собранные файлы
    template = await fs.readFile(
      path.resolve("dist/client/index.html"),
      "utf-8"
    );
    const serverEntry = await import(
      path.resolve("dist/server/entry-server.mjs")
    );
    render = serverEntry.render;

    // Статические файлы для production (бандл)
    app.use(
      "/assets",
      express.static(path.resolve("dist/client/assets"), {
        maxAge: "1y",
        immutable: true,
      })
    );
  }
  function renderPreloadLinks(modules = new Set(), manifest = {}) {
    let links = "";
    const seen = new Set();
    (modules || []).forEach((id) => {
      const files = manifest[id];
      if (!files) return;
      for (const file of files) {
        if (seen.has(file)) continue;
        seen.add(file);
        if (file.endsWith(".js")) {
          links += `<link rel="modulepreload" crossorigin href="/${file}">`;
        } else if (file.endsWith(".css")) {
          // non-blocking CSS
          links +=
            `<link rel="preload" as="style" href="/${file}" onload="this.onload=null;this.rel='stylesheet'">` +
            `<noscript><link rel="stylesheet" href="/${file}"></noscript>`;
        } else if (file.endsWith(".woff2") || file.endsWith(".woff")) {
          const type = file.endsWith(".woff2") ? "font/woff2" : "font/woff";
          links += `<link rel="preload" href="/${file}" as="font" type="${type}" crossorigin>`;
        }
      }
    });
    return links;
  }

  // Нормализация жанров: сводим регистр/число/варианты к каноническому виду
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

      история: "История",
      исторический: "История",
      исторические: "История",

      семейный: "Семейный",
      семейные: "Семейный",

      военный: "Военный",
      военные: "Военный",
      военная: "Военный",
      военное: "Военный",
      war: "Военный",
      military: "Военный",

      биографии: "Биография",
      биографические: "Биография",

      вестерны: "Вестерн",

      документальный: "Документальные",

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

      спорт: "Спорт",
      аниме: "Аниме",
      мультфильмы: "Мультфильмы",
      мультфильм: "Мультфильмы",
      дорама: "Дорамы",
      дорамы: "Дорамы",
      "турецкие сериалы": "Турецкие сериалы",
    };

    if (MAP[key]) return MAP[key];

    // Фолбэк: просто делаем "Первая буква заглавная", остальное нижний регистр
    return key ? key[0].toUpperCase() + key.slice(1) : "";
  }

  function normalizeMovieGenres(list) {
    const arr = Array.isArray(list) ? list : [];
    const out = [];
    const seen = new Set();
    for (const g of arr) {
      const canon = normalizeGenreLabel(g);
      if (canon && !seen.has(canon)) {
        seen.add(canon);
        out.push(canon);
      }
    }
    return out;
  }

  function hasGenreIntersection(a, b) {
    const A = new Set(normalizeMovieGenres(a));
    for (const g of normalizeMovieGenres(b)) {
      if (A.has(g)) return true;
    }
    return false;
  }

  // Middleware
  app.use(cors());
  app.use(express.json());
  if (isProduction) {
    app.use(compression());
  }

  // Статические файлы для production (если не в development режиме)
  if (isProduction) {
    // Кеш для ассетов/картинок
    app.use(
      "/assets",
      express.static(path.join(__dirname, "assets"), {
        maxAge: "30d",
        immutable: true,
      })
    );
    app.use(
      "/uploads",
      express.static(path.join(__dirname, "uploads"), {
        maxAge: "30d",
        immutable: true,
      })
    );
  }

  // Путь к файлу с данными
  const DATA_FILE =
    process.env.DATA_FILE || path.join(__dirname, "movies-data.json");
  // Серверные (только backend) хранилища, чтобы не триггерить HMR фронтенда
  const DATA_DIR = path.join(__dirname, "server-data");
  const COMMENTS_FILE = path.join(DATA_DIR, "comments-store.json");
  const RATINGS_FILE = path.join(DATA_DIR, "ratings-store.json");

  // Вспомогательные функции работы с русской датой премьеры и окном "сегодня/вчера"
  const RU_MONTH = {
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
  function parseRussianPremiere(dateString) {
    if (!dateString) return null;
    const parts = String(dateString).split(" ");
    if (parts.length < 3) return null;
    const day = String(parts[0]).padStart(2, "0");
    const month = RU_MONTH[parts[1]];
    const year = parts[2];
    if (!month) return null;
    const iso = `${year}-${month}-${day}`;
    const d = new Date(iso);
    return isNaN(d.getTime()) ? null : d;
  }
  function isTodayOrYesterday(date) {
    if (!date) return false;
    const todayStart = new Date();
    todayStart.setHours(0, 0, 0, 0);
    const yesterdayStart = new Date(todayStart);
    yesterdayStart.setDate(todayStart.getDate() - 1);
    return date >= yesterdayStart;
  }
  function isHidden(movie) {
    return !!(movie && movie.hidden);
  }
  // helpers for feeds
  function ratingOf(m) {
    const i = parseFloat(String(m.imdbRating || "").replace(",", ".")) || 0;
    const k = parseFloat(String(m.kpRating || "").replace(",", ".")) || 0;
    return Math.max(i, k);
  }
  const ASIAN_KEYWORDS = [
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
  function isAsianCountry(countryStr) {
    if (!countryStr) return false;
    const s = String(countryStr).toLowerCase();
    return ASIAN_KEYWORDS.some((k) => s.includes(k));
  }
  function isTurkish(countryStr) {
    return /турция/i.test(countryStr || "");
  }
  function isRussianCountry(countryStr) {
    return /росси/i.test(countryStr || "");
  }
  function passPopularity(m, special) {
    const p = Number(m.popularity || 0);
    if (String(special) === "doramas") {
      const t = Number(
        process.env.HOME_POP_DORAMAS || process.env.HOME_POP_DEFAULT || 5
      );
      return p >= t;
    }
    if (String(special) === "turkish") {
      const t = Number(
        process.env.HOME_POP_TURKISH || process.env.HOME_POP_DEFAULT || 5
      );
      return p >= t;
    }
    const tRu = Number(process.env.HOME_POP_RU || 4);
    const tDefault = Number(process.env.HOME_POP_DEFAULT || 12);
    return isRussianCountry(m.country) ? p >= tRu : p >= tDefault;
  }
  function cardFields(m) {
    return {
      id: m.id,
      category: m.category,
      title: m.title,
      year: m.year,
      image: m.image,
      kpRating: m.kpRating,
      imdbRating: m.imdbRating,
      genres: m.genres,
      country: m.country,
      premiere: m.premiere,
      season: m.season,
      episode: m.episode,
    };
  }
  function categoryCardFields(m) {
    return {
      id: m.id,
      category: m.category,
      title: m.title,
      year: m.year,
      image: m.image,
      kpRating: m.kpRating,
      imdbRating: m.imdbRating,
      genres: m.genres,
      country: m.country,
      premiere: m.premiere,
      season: m.season,
      episode: m.episode,
      description: m.description,
      originalTitle: m.originalTitle,
      director: m.director,
      translation: m.translation,
      actors: m.actors,
      trailer: m.trailer,
    };
  }
  function pickLatest(list, count = 24) {
    const toTime = (m) => {
      const d = parseRussianPremiere(m.premiere);
      return d
        ? d.getTime()
        : m.year
        ? new Date(`${m.year}-01-01`).getTime()
        : 0;
    };
    return [...list].sort((a, b) => toTime(b) - toTime(a)).slice(0, count);
  }
  function upsertPreconnects(html, origins = []) {
    const exists = (o) =>
      new RegExp(
        `<link\\s+rel=["']preconnect["'][^>]*href=["']${o.replace(
          /[.*+?^${}()|[\]\\]/g,
          "\\$&"
        )}["']`,
        "i"
      ).test(html);
    const tags = origins
      .filter(Boolean)
      .filter((o) => !exists(o))
      .map((o) => `<link rel="preconnect" href="${o}" crossorigin>`)
      .join("\n  ");
    if (!tags) return html;
    return html.replace("</head>", `  ${tags}\n</head>`);
  }
  function buildCategoryFeed(data, opts) {
    const {
      name,
      page = 1,
      limit = 24,
      sort = "year",
      year,
      genre,
      country,
      translation,
      actor,
      special,
    } = opts;

    const movies = (data?.movies || []).filter(
      (m) => m.category === name && m.id !== "index" && !isHidden(m)
    );

    const availableYears = [
      ...new Set(movies.map((m) => m.year).filter(Boolean)),
    ].sort((a, b) => b - a);

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

    const availableGenres = Array.from(
      movies.reduce((acc, m) => {
        normalizeMovieGenres(m.genres)
          .filter((g) => !EXCLUDED_GENRES.has(g))
          .forEach((g) => acc.add(g));
        return acc;
      }, new Set())
    )
      .filter((g) => !(name === "anime" && g === "Аниме"))
      .filter((g) => !(name === "multfilmy" && g === "Мультфильмы"))
      .sort();

    let filtered = [...movies];

    if (special === "doramas") {
      filtered = filtered.filter(
        (m) => isAsianCountry(m.country) && !isTurkish(m.country)
      );
    } else if (special === "turkish") {
      filtered = filtered.filter((m) => isTurkish(m.country));
    }

    if (year)
      filtered = filtered.filter((m) => String(m.year) === String(year));
    if (genre) {
      const needle = normalizeGenreLabel(String(genre));
      filtered = filtered.filter((m) =>
        normalizeMovieGenres(m.genres).includes(needle)
      );
    }
    if (country)
      filtered = filtered.filter((m) =>
        String(m.country || "")
          .toLowerCase()
          .includes(String(country).toLowerCase())
      );
    if (translation)
      filtered = filtered.filter((m) => {
        const t = m.translation;
        const needle = String(translation).toLowerCase();
        if (!t) return false;
        if (Array.isArray(t))
          return t.some((x) => String(x).toLowerCase().includes(needle));
        return String(t).toLowerCase().includes(needle);
      });
    if (actor)
      filtered = filtered.filter((m) =>
        String(m.actors || "").includes(String(actor))
      );

    // Ограничение для вкладки "По рейтингу" на главной: только последние N лет
    if (opts.home && sort === "rating") {
      const currentYear = new Date().getFullYear();
      const span = Math.max(
        1,
        parseInt(process.env.HOME_RATING_YEARS, 10) || 3
      );
      const minYear = currentYear - span + 1;
      filtered = filtered.filter((m) => Number(m.year || 0) >= minYear);
    }

    // Ограничение для вкладки "Популярные" на главной: только последние N лет
    if (opts.home && sort === "popularity") {
      const currentYear = new Date().getFullYear();
      const span = Math.max(
        1,
        parseInt(process.env.HOME_POP_YEARS, 10) || 2 // по умолчанию последние 2 года
      );
      const minYear = currentYear - span + 1;
      filtered = filtered.filter((m) => Number(m.year || 0) >= minYear);
    }

    if (opts.home) {
      filtered = filtered.filter((m) => passPopularity(m, special));
    }

    filtered.sort((a, b) => {
      switch (sort) {
        case "rating": {
          const ra = Math.max(
            parseFloat(a.imdbRating) || 0,
            parseFloat(a.kpRating) || 0
          );
          const rb = Math.max(
            parseFloat(b.imdbRating) || 0,
            parseFloat(b.kpRating) || 0
          );
          return rb - ra;
        }
        case "popularity":
          return (b.popularity || 0) - (a.popularity || 0);
        case "title":
          return String(a.title).localeCompare(String(b.title));
        case "year":
        default:
          return (b.year || 0) - (a.year || 0);
      }
    });

    const total = filtered.length;
    const totalPages = Math.max(1, Math.ceil(total / limit));
    const pageNumber = Math.min(
      Math.max(1, parseInt(page, 10) || 1),
      totalPages
    );
    const start = (pageNumber - 1) * limit;
    const items = filtered.slice(start, start + limit).map(categoryCardFields);

    return {
      category: name,
      title: (data?.categories || {})[name] || "Контент",
      page: pageNumber,
      limit,
      total,
      totalPages,
      availableYears,
      availableGenres,
      items,
    };
  }

  function buildMoviePayload(data, id) {
    const movie = (data?.movies || []).find((m) => m.id === id);
    if (!movie || isHidden(movie)) return null;

    const categories = data?.categories || {};

    let related = [];
    if (relatedMapCache && relatedMapCache[movie.id]) {
      related = mapIdsToCards(data, relatedMapCache[movie.id]);
    }
    if (!related.length) {
      related = (data?.movies || [])
        .filter(
          (m) =>
            m.id !== movie.id &&
            m.category === movie.category &&
            hasGenreIntersection(m.genres, movie.genres) &&
            !isHidden(m)
        )
        .slice(0, 6)
        .map(categoryCardFields);
    }

    return { movie, categories, related };
  }

  function buildHomeFeed(data) {
    const all = (data?.movies || []).filter(
      (m) => m.id !== "index" && !isHidden(m)
    );
    const allowed = all.filter((m) => passPopularity(m));
    const allowedDoramas = all.filter((m) => passPopularity(m, "doramas"));
    const allowedTurkish = all.filter((m) => passPopularity(m, "turkish"));

    const thirty = new Date();
    thirty.setDate(thirty.getDate() - 30);
    const recent = allowed.filter((m) => {
      const d = parseRussianPremiere(m.premiere);
      return d && d >= thirty;
    });

    let popular = recent
      .sort((a, b) => (b.popularity || 0) - (a.popularity || 0))
      .slice(0, 12);
    if (popular.length < 12) {
      const ids = new Set(popular.map((m) => m.id));
      const add = allowed
        .filter((m) => !ids.has(m.id))
        .sort((a, b) => (b.popularity || 0) - (a.popularity || 0))
        .slice(0, 12 - popular.length);
      popular = popular.concat(add);
    }
    const cat = (name) =>
      pickLatest(allowed.filter((m) => m.category === name));
    const doramas = pickLatest(
      allowedDoramas.filter(
        (m) =>
          m.category === "serialy" &&
          isAsianCountry(m.country) &&
          !isTurkish(m.country)
      )
    );
    const turkish = pickLatest(
      allowedTurkish.filter(
        (m) => m.category === "serialy" && isTurkish(m.country)
      )
    );
    return {
      popular: popular.map(categoryCardFields),
      sections: {
        filmy: { latest: cat("filmy").map(categoryCardFields) },
        serialy: { latest: cat("serialy").map(categoryCardFields) },
        multfilmy: { latest: cat("multfilmy").map(categoryCardFields) },
        anime: { latest: cat("anime").map(categoryCardFields) },
        doramas: { latest: doramas.map(categoryCardFields) },
        turkish: { latest: turkish.map(categoryCardFields) },
      },
    };
  }
  function buildTopFeedPaged(
    data,
    { limit = 24, offset = 0, type = "all" } = {}
  ) {
    let list = (data?.movies || []).filter(
      (m) => m.id !== "index" && ratingOf(m) > 0 && !isHidden(m)
    );
    switch (type) {
      case "filmy":
      case "serialy":
      case "multfilmy":
      case "anime":
        list = list.filter((m) => m.category === type);
        break;
      case "doramas":
        list = list.filter(
          (m) =>
            m.category === "serialy" &&
            isAsianCountry(m.country) &&
            !isTurkish(m.country)
        );
        break;
      case "turkish":
        list = list.filter(
          (m) => m.category === "serialy" && isTurkish(m.country)
        );
        break;
      default:
        break;
    }
    const sorted = list
      .map((m) => ({ movie: m, r: ratingOf(m) }))
      .sort((a, b) => b.r - a.r)
      .map((x) => x.movie);
    const total = sorted.length;
    const items = sorted.slice(offset, offset + limit).map(categoryCardFields);
    return { items, total };
  }

  let moviesDataCache = null;
  const categoryFeedCache = new Map();
  let homeFeedCache = { mtime: null, data: null };
  const topFeedCache = new Map(); // ← добавь эту строку
  let lastModifiedTime = null;

  // === SSR micro-cache (1–3s) for non-bots ===
  const SSR_TTL_MS = 2000;
  const ssrCache = new Map();

  function ssrKey(url) {
    return `${url}#${lastModifiedTime || 0}`;
  }

  // вместо хранения только html:
  function setSsrToCache(url, html, status = 200) {
    const k = ssrKey(url);
    ssrCache.set(k, { ts: Date.now(), html, status });
  }

  function getSsrFromCache(url) {
    const k = ssrKey(url);
    const rec = ssrCache.get(k);
    if (rec && Date.now() - rec.ts < SSR_TTL_MS) return rec;
    if (rec) ssrCache.delete(k);
    return null;
  }

  // === Cache caps and helpers (insert after L591) ===
  const MAX_CATEGORY_CACHE = 200;
  const MAX_TOP_CACHE = 100;

  const MAX_SEARCH_CACHE = 500;
  const SEARCH_TTL_MS = 60_000;
  const searchCache = new Map();

  function setWithCap(map, key, value, cap) {
    if (map.size >= cap && !map.has(key)) {
      const firstKey = map.keys().next().value;
      map.delete(firstKey);
    }
    map.set(key, value);
  }

  function setDataCacheHeaders(res, ttl = 60) {
    if (lastModifiedTime) {
      res.set("Last-Modified", new Date(lastModifiedTime).toUTCString());
    }
    res.set("Cache-Control", `public, max-age=${ttl}`);
  }

  function tryConditional304(req, res) {
    if (!lastModifiedTime) return false;
    const since = req.headers["if-modified-since"];
    if (!since) return false;
    const sinceMs = Date.parse(since);
    if (!isNaN(sinceMs) && sinceMs >= lastModifiedTime) {
      res.status(304).end();
      return true;
    }
    return false;
  }

  let sharpConfigured = false;

  function getHomeFeed(data) {
    if (homeFeedCache.data && homeFeedCache.mtime === lastModifiedTime) {
      return homeFeedCache.data;
    }
    const feed = buildHomeFeed(data);
    homeFeedCache = { mtime: lastModifiedTime, data: feed };
    return feed;
  }

  function getCategoryFeed(data, opts) {
    const key = JSON.stringify(opts);
    const cached = categoryFeedCache.get(key);
    if (cached && cached.mtime === lastModifiedTime) return cached.data;
    const feed = buildCategoryFeed(data, opts);
    setWithCap(
      categoryFeedCache,
      key,
      { mtime: lastModifiedTime, data: feed },
      MAX_CATEGORY_CACHE
    );
    return feed;
  }

  function getTopFeedPaged(data, options) {
    const key = JSON.stringify({ ...options });
    const cached = topFeedCache.get(key);
    if (cached && cached.mtime === lastModifiedTime) {
      return cached.data;
    }
    const feed = buildTopFeedPaged(data, options);
    setWithCap(
      topFeedCache,
      key,
      { mtime: lastModifiedTime, data: feed },
      MAX_TOP_CACHE
    );
    return feed;
  }

  // put this near other cache vars
  let dataLoadPromise = null;

  async function readData() {
    try {
      const stats = await fs.stat(DATA_FILE);

      // Cache hit
      if (moviesDataCache && lastModifiedTime === stats.mtimeMs) {
        return moviesDataCache;
      }

      // If a load is already in flight, wait for it
      if (dataLoadPromise) {
        return await dataLoadPromise;
      }

      // Start a single load for all concurrent callers
      dataLoadPromise = (async () => {
        console.log(
          moviesDataCache
            ? "movies-data.json changed, reloading cache..."
            : "Loading movies-data.json into cache..."
        );
        const raw = await fs.readFile(DATA_FILE, "utf8");
        const parsed = JSON.parse(raw);
        moviesDataCache = parsed;
        lastModifiedTime = stats.mtimeMs;
        dataLoadPromise = null;
        return moviesDataCache;
      })();

      return await dataLoadPromise;
    } catch (error) {
      dataLoadPromise = null;
      if (error?.code === "ENOENT") {
        console.warn("movies-data.json not found at:", DATA_FILE);
      } else {
        console.error("Ошибка чтения файла:", error);
      }
      moviesDataCache = null;
      lastModifiedTime = null;
      return null;
    }
  }
  // server.js
  const RELATED_MAP_FILE = path.join(DATA_DIR, "related-map.json");
  let relatedMapCache = null;
  let relatedMapMtime = null;
  let relatedMapLoadPromise = null;

  async function readRelatedMap() {
    try {
      const stats = await fs.stat(RELATED_MAP_FILE);
      if (relatedMapCache && relatedMapMtime === stats.mtimeMs)
        return relatedMapCache;
      if (relatedMapLoadPromise) return await relatedMapLoadPromise;
      relatedMapLoadPromise = (async () => {
        const raw = await fs.readFile(RELATED_MAP_FILE, "utf8");
        relatedMapCache = JSON.parse(raw);
        relatedMapMtime = stats.mtimeMs;
        relatedMapLoadPromise = null;
        return relatedMapCache;
      })();
      return await relatedMapLoadPromise;
    } catch {
      relatedMapLoadPromise = null;
      relatedMapCache = relatedMapCache || {};
      return relatedMapCache;
    }
  }

  // Хелперы для серверных стораджей
  async function ensureDataDir() {
    try {
      await fs.mkdir(DATA_DIR, { recursive: true });
    } catch (_) {}
  }

  async function readStore(filePath, fallbackValue) {
    await ensureDataDir();
    try {
      const raw = await fs.readFile(filePath, "utf8");
      return JSON.parse(raw);
    } catch (error) {
      return fallbackValue;
    }
  }

  function mapIdsToCards(data, ids) {
    const byId = new Map((data?.movies || []).map((m) => [m.id, m]));
    return (ids || [])
      .map((id) => byId.get(id))
      .filter((m) => m && !isHidden(m))
      .slice(0, 6)
      .map(categoryCardFields);
  }

  async function writeStore(filePath, data) {
    await ensureDataDir();
    await fs.writeFile(filePath, JSON.stringify(data, null, 2), "utf8");
  }

  // Комментарии: хранение по ключу movieId -> Comment[]
  async function getCommentsStore() {
    return readStore(COMMENTS_FILE, {});
  }

  async function setCommentsStore(store) {
    await writeStore(COMMENTS_FILE, store);
  }

  function transformStylesheetsToPreload(html) {
    let keptOnce = false;
    return html.replace(
      /<link\s+rel=["']stylesheet["'][^>]*href=["'](\/assets\/[^"']+\.css)["'][^>]*>\s*/gi,
      (m, href) => {
        if (!keptOnce) {
          keptOnce = true;
          return m;
        }
        const hasCross = /crossorigin/i.test(m) ? " crossorigin" : "";
        const mediaMatch = m.match(/\smedia=["']([^"']+)["']/i);
        const mediaAttr = mediaMatch ? ` media="${mediaMatch[1]}"` : "";
        return (
          `<link rel="preload" as="style" href="${href}"${hasCross}${mediaAttr} onload="this.onload=null;this.rel='stylesheet'">` +
          `<noscript><link rel="stylesheet" href="${href}"${hasCross}${mediaAttr}></noscript>`
        );
      }
    );
  }

  async function getCommentsForMovie(movieId) {
    const store = await getCommentsStore();
    if (!store[movieId]) {
      // Ленивая инициализация из movies-data.json (если есть)
      const data = await readData();
      const movie = data?.movies.find((m) => m.id === movieId);
      store[movieId] = movie?.comments || [];
      await setCommentsStore(store);
    }
    return store[movieId];
  }

  async function saveCommentsForMovie(movieId, comments) {
    const store = await getCommentsStore();
    store[movieId] = comments;
    await setCommentsStore(store);
    return comments;
  }

  // Рейтинги страниц: хранение по ключу movieId -> { pageLikes, pageDislikes }
  async function getRatingsStore() {
    return readStore(RATINGS_FILE, {});
  }

  async function setRatingsStore(store) {
    await writeStore(RATINGS_FILE, store);
  }

  async function getRatingsForMovie(movieId) {
    const store = await getRatingsStore();
    if (!store[movieId]) {
      // Ленивая инициализация из movies-data.json (если есть)
      const data = await readData();
      const movie = data?.movies.find((m) => m.id === movieId);
      store[movieId] = {
        pageLikes: movie?.pageLikes || 0,
        pageDislikes: movie?.pageDislikes || 0,
      };
      await setRatingsStore(store);
    }
    return store[movieId];
  }

  async function saveRatingsForMovie(movieId, ratings) {
    const store = await getRatingsStore();
    store[movieId] = ratings;
    await setRatingsStore(store);
    return ratings;
  }

  async function verifyRecaptcha(token, secretKey) {
    const url = "https://www.google.com/recaptcha/api/siteverify";

    try {
      const response = await axios.post(url, null, {
        params: {
          secret: secretKey,
          response: token,
        },
      });
      return response.data;
    } catch (error) {
      console.error("Error verifying reCAPTCHA:", error);
      return { success: false, "error-codes": ["request-failed"] };
    }
  }

  function stripBlockingCssLinks(html) {
    // Удаляем любые rel="stylesheet" на /assets/*.css
    return html.replace(
      /<link\s+rel=["']stylesheet["'][^>]*href=["']\/assets\/[^"']+\.css["'][^>]*>\s*/gi,
      ""
    );
  }

  function injectPreloadLinks(html, preload) {
    if (!preload) return html;
    if (html.includes("<!--preload-links-->")) {
      return html.replace("<!--preload-links-->", preload);
    }
    // Если плейсхолдера нет, вставляем перед </head>
    return html.replace("</head>", `${preload}\n</head>`);
  }

  // Простой кэш, чтобы не перечитывать файл каждый раз
  const kodikUrlCache = new Map();
  const KODIK_BIG_FILE = path.join(
    __dirname,
    "movies-data-without-pop-pretty-updated.json"
  );

  app.get("/api/probe-sv", async (req, res) => {
    try {
      const kp = String(req.query.kp || "");
      const publisherId = String(req.query.publisherId || "79");
      if (!kp) return res.status(400).json({ ok: false, error: "missing kp" });

      const { JSDOM } = require("jsdom");
      const dom = new JSDOM(
        `<!doctype html><html><body><div id="root"></div></body></html>`,
        {
          url: BASE_URL,
          runScripts: "outside-only",
          pretendToBeVisual: true,
        }
      );
      const { window } = dom;
      const { document } = window;

      // Полифилы для среды выполнения плеера
      const { TextDecoder, TextEncoder } = require("util");
      window.TextDecoder = window.TextDecoder || TextDecoder;
      window.TextEncoder = window.TextEncoder || TextEncoder;
      globalThis.TextDecoder = globalThis.TextDecoder || TextDecoder;
      globalThis.TextEncoder = globalThis.TextEncoder || TextEncoder;

      window.atob =
        window.atob ||
        ((s) => Buffer.from(String(s), "base64").toString("binary"));
      window.btoa =
        window.btoa ||
        ((s) => Buffer.from(String(s), "binary").toString("base64"));

      const nodeCrypto = require("crypto");
      window.crypto = window.crypto || nodeCrypto.webcrypto;
      globalThis.crypto = window.crypto;

      window.self = window;

      window.IntersectionObserver = class {
        constructor() {}
        observe() {}
        disconnect() {}
      };
      window.MutationObserver = class {
        constructor() {}
        observe() {}
        disconnect() {}
      };
      window.requestAnimationFrame = (cb) => setTimeout(cb, 16);

      // Грузим UMD и UI (оба нужны)
      const [umd, ui] = await Promise.all([
        axios.get(`${BASE_URL}/api/cdnvh-umd.js`, {
          timeout: 15000,
          headers: { "User-Agent": "Mozilla/5.0", Referer: BASE_URL },
          responseType: "text",
          validateStatus: () => true,
        }),
        axios.get(`${BASE_URL}/api/cdnvh-playerui.js`, {
          timeout: 15000,
          headers: { "User-Agent": "Mozilla/5.0", Referer: BASE_URL },
          responseType: "text",
          validateStatus: () => true,
        }),
      ]);
      if (umd.status >= 400 || !umd.data)
        return res.json({
          ok: false,
          error: "umd-fetch-failed",
          status: umd.status,
        });
      if (ui.status >= 400 || !ui.data)
        return res.json({
          ok: false,
          error: "ui-fetch-failed",
          status: ui.status,
        });

      window.eval(umd.data);
      window.eval(ui.data);

      // Создаём элемент плеера
      const el = document.createElement("video-player");
      el.setAttribute("data-publisher-id", publisherId);
      el.setAttribute("data-title-id", kp);
      el.setAttribute("data-aggregator", "kp");
      el.setAttribute("is-show-banner", "false");
      document.getElementById("root").appendChild(el);

      // Поиск iframe внутри shadowRoot или документа
      function findMainIframe() {
        const vp = document.querySelector("video-player");
        const roots = [];
        if (vp && vp.shadowRoot) roots.push(vp.shadowRoot);
        roots.push(document);
        for (const root of roots) {
          const ifr = root.querySelector(
            'iframe.vk-player-iframe, iframe[src*="vk.com"], iframe[src*="cdnvideohub"], iframe[src*="vkvideo"]'
          );
          if (ifr) return ifr;
        }
        return null;
      }

      const started = Date.now();
      let foundSrc = null;
      async function poll(maxMs = 6000) {
        while (Date.now() - started < maxMs) {
          const ifr = findMainIframe();
          if (ifr && ifr.getAttribute("src")) {
            foundSrc = ifr.getAttribute("src");
            break;
          }
          await new Promise((r) => setTimeout(r, 200));
        }
      }
      await poll(6000);

      if (!foundSrc) return res.json({ ok: false, reason: "no-main-iframe" });

      const probe = await axios.get(`${BASE_URL}/api/probe-player`, {
        params: { url: foundSrc, debug: "1" },
        timeout: 10000,
        validateStatus: () => true,
      });

      res.json({
        ok: !!(probe.data || {}).ok,
        iframe: foundSrc,
        probe: probe.data || {},
      });
    } catch (e) {
      res.json({ ok: false, error: e?.message || "probe-sv-failed" });
    }
  });

  // GET /api/kodik-url/:id — достаёт kodikPlayer из большого файла по id
  app.get("/api/kodik-url/:id", async (req, res) => {
    try {
      const id = String(req.params.id);
      if (!id) return res.status(400).json({ error: "missing id" });

      if (kodikUrlCache.has(id)) {
        return res.json({ url: kodikUrlCache.get(id) });
      }

      const raw = await fs.readFile(KODIK_BIG_FILE, "utf8");

      // Ищем блок по id и берем ближайший kodikPlayer
      const needle = `"id": "${id}"`;
      const pos = raw.indexOf(needle);
      if (pos === -1) return res.status(404).json({ error: "not_found" });

      const slice = raw.slice(pos, pos + 8000); // локальный отрезок после id
      const m = slice.match(/"kodikPlayer"\s*:\s*"([^"]+)"/);
      if (!m) return res.status(404).json({ error: "no_kodik_url" });

      const url = m[1];
      kodikUrlCache.set(id, url);
      res.json({ url });
    } catch (e) {
      res.status(500).json({ error: "server_error" });
    }
  });

  app.get("/api/movies-data", async (req, res) => {
    try {
      if (tryConditional304(req, res)) return;
      const data = await readData();
      const includeHidden = String(req.query.includeHidden || "") === "1";
      const movies = includeHidden
        ? data.movies || []
        : (data.movies || []).filter((m) => !m.hidden);
      setDataCacheHeaders(res, 60);
      res.json({ ...data, movies });
    } catch (e) {
      res.status(500).json({ movies: [], categories: {} });
    }
  });

  app.get("/api/search", async (req, res) => {
    try {
      const q = String(req.query.q || "").toLowerCase();
      if (!q) return res.json([]);
      if (tryConditional304(req, res)) return;
      setDataCacheHeaders(res, 30);

      const cached = searchCache.get(q);
      if (
        cached &&
        Date.now() - cached.ts < SEARCH_TTL_MS &&
        cached.mtime === lastModifiedTime
      ) {
        return res.json(cached.data);
      }

      const data = await readData();

      const norm = (v) => String(v ?? "").toLowerCase();
      const normActors = (v) =>
        Array.isArray(v)
          ? v.join(", ").toLowerCase()
          : String(v ?? "").toLowerCase();

      const found = (data.movies || [])
        .filter(
          (m) =>
            m.id !== "index" &&
            !isHidden(m) &&
            (norm(m.title).includes(q) ||
              norm(m.originalTitle).includes(q) ||
              norm(m.description).includes(q) ||
              normActors(m.actors).includes(q))
        )
        .slice(0, 200)
        .map((m) => ({
          id: m.id,
          category: m.category,
          title: m.title,
          year: m.year,
          image: m.image,
          kpRating: m.kpRating,
          imdbRating: m.imdbRating,
        }));

      setWithCap(
        searchCache,
        q,
        { ts: Date.now(), data: found, mtime: lastModifiedTime },
        MAX_SEARCH_CACHE
      );
      res.json(found);
    } catch (e) {
      res.status(500).json([]);
    }
  });

  // GET /api/movie/:id — один фильм
  app.get("/api/movie/:id", async (req, res) => {
    if (tryConditional304(req, res)) return;
    const data = await readData();
    const m = (data?.movies || []).find((x) => x.id === req.params.id);
    if (!m || isHidden(m)) return res.status(404).json({ error: "not_found" });
    setDataCacheHeaders(res, 60);
    res.json({ movie: m, categories: data?.categories || {} });
  });

  // Home feed for landing page
  app.get("/api/home-feed", async (req, res) => {
    try {
      if (tryConditional304(req, res)) return;
      const data = await readData();
      setDataCacheHeaders(res, 60);
      res.json(getHomeFeed(data));
    } catch {
      res.status(500).json({ popular: [], sections: {} });
    }
  });

  app.get("/api/movie-full/:id", async (req, res) => {
    try {
      if (tryConditional304(req, res)) return;
      const data = await readData();
      await readRelatedMap(); // добавить эту строку
      const payload = buildMoviePayload(data, String(req.params.id));
      if (!payload) return res.status(404).json({ error: "not_found" });
      setDataCacheHeaders(res, 60);
      res.json(payload);
    } catch {
      res.status(500).json({ error: "server_error" });
    }
  });

  app.get("/api/category", async (req, res) => {
    try {
      const data = await readData();
      if (tryConditional304(req, res)) return;
      const name = String(req.query.name || "").trim();
      if (!name) return res.status(400).json({ error: "missing name" });

      const limit = Math.max(
        1,
        Math.min(200, parseInt(req.query.limit, 10) || 24)
      );
      const page = Math.max(1, parseInt(req.query.page, 10) || 1);
      const sort = String(req.query.sort || "year");

      const opts = {
        name,
        page,
        limit,
        sort,
        year: req.query.year,
        genre: req.query.genre,
        country: req.query.country,
        translation: req.query.translation,
        actor: req.query.actor,
        special: req.query.special,
        home: String(req.query.home || "") === "1",
      };

      const feed = getCategoryFeed(data, opts);
      setDataCacheHeaders(res, 60);
      res.json(feed);
    } catch (e) {
      res.status(500).json({ items: [], total: 0, totalPages: 1 });
    }
  });

  // Top list
  app.get("/api/top", async (req, res) => {
    try {
      const data = await readData();
      if (tryConditional304(req, res)) return;
      const limit = Math.max(
        1,
        Math.min(200, parseInt(req.query.limit, 10) || 24)
      );
      const offset = Math.max(0, parseInt(req.query.offset, 10) || 0);
      const type = String(req.query.type || "all");
      const result = getTopFeedPaged(data, { limit, offset, type });
      setDataCacheHeaders(res, 60);
      res.json(result);
    } catch {
      res.status(500).json({ items: [], total: 0 });
    }
  });

  // Related movies for a given id (prefer static map)
  app.get("/api/related/:id", async (req, res) => {
    try {
      if (tryConditional304(req, res)) return;
      const data = await readData();
      await readRelatedMap(); // добавить эту строку
      const id = String(req.params.id);
      const list = data?.movies || [];
      const cur = list.find((m) => m.id === id);
      if (!cur || isHidden(cur)) {
        setDataCacheHeaders(res, 60);
        return res.json({ items: [] });
      }

      let items = [];
      if (relatedMapCache && relatedMapCache[id]) {
        items = mapIdsToCards(data, relatedMapCache[id]);
      }
      if (!items.length) {
        items = list
          .filter(
            (m) =>
              m.id !== id &&
              m.category === cur.category &&
              hasGenreIntersection(m.genres, cur.genres) &&
              !isHidden(m)
          )
          .slice(0, 6)
          .map((m) => ({
            id: m.id,
            category: m.category,
            title: m.title,
            year: m.year,
            image: m.image,
            kpRating: m.kpRating,
            imdbRating: m.imdbRating,
            genres: m.genres,
          }));
      }

      setDataCacheHeaders(res, 60);
      res.json({ items });
    } catch {
      setDataCacheHeaders(res, 60);
      res.status(500).json({ items: [] });
    }
  });

  // GET /api/movies — список с пагинацией и фильтрами
  // /api/movies?category=filmy&page=1&limit=24&year=2024&genre=Драма&country=Турция&sort=rating
  app.get("/api/movies", async (req, res) => {
    const {
      category = "",
      page = 1,
      limit = 24,
      year,
      genre,
      country,
      q,
      sort,
    } = req.query;
    const data = await readData();
    let list = (data?.movies || []).filter(
      (m) => m.id !== "index" && !isHidden(m)
    );

    if (category) list = list.filter((m) => m.category === String(category));
    if (year) list = list.filter((m) => String(m.year) === String(year));
    if (genre) {
      const needle = normalizeGenreLabel(String(genre));
      list = list.filter((m) =>
        normalizeMovieGenres(m.genres).includes(needle)
      );
    }
    if (country)
      list = list.filter((m) =>
        (m.country || "").toLowerCase().includes(String(country).toLowerCase())
      );
    if (q) {
      const s = String(q).toLowerCase();
      const actors = (v) =>
        Array.isArray(v)
          ? v.join(",").toLowerCase()
          : String(v || "").toLowerCase();
      list = list.filter(
        (m) =>
          String(m.title || "")
            .toLowerCase()
            .includes(s) ||
          String(m.originalTitle || "")
            .toLowerCase()
            .includes(s) ||
          actors(m.actors).includes(s)
      );
    }
    if (sort === "rating") {
      const rating = (m) => {
        const i = parseFloat(String(m.imdbRating || "").replace(",", ".")) || 0;
        const k = parseFloat(String(m.kpRating || "").replace(",", ".")) || 0;
        return Math.max(i, k);
      };
      list = list
        .map((m) => ({ m, r: rating(m) }))
        .filter((x) => x.r > 0)
        .sort((a, b) => b.r - a.r)
        .map((x) => x.m);
    } else if (sort === "popularity") {
      list = list.sort((a, b) => (b.popularity || 0) - (a.popularity || 0));
    } else if (sort === "new") {
      list = list.sort((a, b) => (b.year || 0) - (a.year || 0));
    }

    const p = Math.max(1, parseInt(page, 10) || 1);
    const L = Math.max(1, Math.min(100, parseInt(limit, 10) || 24));
    const total = list.length;
    const totalPages = Math.max(1, Math.ceil(total / L));
    const items = list.slice((p - 1) * L, (p - 1) * L + L).map((m) => ({
      // верни «карточочные» поля, без тяжёлых описаний — легче клиенту
      id: m.id,
      category: m.category,
      title: m.title,
      year: m.year,
      image: m.image,
      kpRating: m.kpRating,
      imdbRating: m.imdbRating,
      genres: m.genres,
      country: m.country,
      premiere: m.premiere,
      season: m.season,
      episode: m.episode,
    }));
    setDataCacheHeaders(res, 60);
    res.json({
      items,
      page: p,
      total,
      totalPages,
      categories: data?.categories || {},
    });
  });

  app.get("/api/search-suggestions", async (req, res) => {
    try {
      const { q } = req.query;
      if (!q || q.length < 1) {
        return res.json([]);
      }
      if (tryConditional304(req, res)) return;
      setDataCacheHeaders(res, 30);

      const key = `sugg:${String(q).toLowerCase()}`;
      const cached = searchCache.get(key);
      if (
        cached &&
        Date.now() - cached.ts < SEARCH_TTL_MS &&
        cached.mtime === lastModifiedTime
      ) {
        return res.json(cached.data);
      }

      const data = await readData();
      if (!data || !data.movies) {
        return res.status(500).json({ error: "Could not load movie data." });
      }

      const suggestions = data.movies
        .filter(
          (movie) =>
            movie.id !== "index" &&
            !isHidden(movie) &&
            (movie.title.toLowerCase().includes(q.toLowerCase()) ||
              (movie.originalTitle &&
                movie.originalTitle.toLowerCase().includes(q.toLowerCase())))
        )
        .slice(0, 5)
        .map((movie) => ({
          id: movie.id,
          title: movie.title,
          category: movie.category,
          year: movie.year,
          poster: movie.image,
          genres: movie.genres ? movie.genres.slice(0, 3) : [],
          kpRating: movie.kpRating,
          imdbRating: movie.imdbRating,
        }));

      setWithCap(
        searchCache,
        key,
        { ts: Date.now(), data: suggestions, mtime: lastModifiedTime },
        MAX_SEARCH_CACHE
      );
      res.json(suggestions);
    } catch (error) {
      console.error("Ошибка поиска:", error);
      res.status(500).json({ error: "Внутренняя ошибка сервера" });
    }
  });

  // API endpoint для голосования за страницу
  app.post("/api/vote-page", async (req, res) => {
    try {
      res.set(
        "Cache-Control",
        "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
      );
      const { movieId, voteType, previousVote } = req.body;

      if (!movieId) {
        return res
          .status(400)
          .json({ error: "Неверные параметры: отсутствует movieId" });
      }

      // voteType может быть null когда пользователь отменяет голос
      if (voteType !== "like" && voteType !== "dislike" && voteType !== null) {
        return res.status(400).json({
          error:
            "Неверные параметры: voteType должен быть like, dislike или null",
        });
      }

      // Читаем/инициализируем серверное хранилище рейтингов
      const ratings = await getRatingsForMovie(movieId);

      // Обновляем оценки
      if (previousVote === "like") ratings.pageLikes--;
      if (previousVote === "dislike") ratings.pageDislikes--;

      if (voteType === "like") ratings.pageLikes++;
      if (voteType === "dislike") ratings.pageDislikes++;

      ratings.pageLikes = Math.max(0, ratings.pageLikes);
      ratings.pageDislikes = Math.max(0, ratings.pageDislikes);

      await saveRatingsForMovie(movieId, ratings);

      res.json({
        success: true,
        pageLikes: ratings.pageLikes,
        pageDislikes: ratings.pageDislikes,
      });
    } catch (error) {
      console.error("Ошибка голосования:", error);
      res.status(500).json({ error: "Внутренняя ошибка сервера" });
    }
  });

  // API endpoint для получения оценок фильма
  app.get("/api/movie-ratings/:movieId", async (req, res) => {
    try {
      res.set(
        "Cache-Control",
        "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
      );
      const { movieId } = req.params;
      const ratings = await getRatingsForMovie(movieId);
      res.json({
        pageLikes: ratings.pageLikes || 0,
        pageDislikes: ratings.pageDislikes || 0,
      });
    } catch (error) {
      console.error("Ошибка получения оценок:", error);
      res.status(500).json({ error: "Внутренняя ошибка сервера" });
    }
  });

  // API endpoint для получения всех оценок
  app.get("/api/all-ratings", async (req, res) => {
    try {
      const ratings = await getRatingsStore();
      res.json(ratings);
    } catch (error) {
      console.error("Ошибка получения всех оценок:", error);
      res.status(500).json({ error: "Внутренняя ошибка сервера" });
    }
  });

  // API endpoint для добавления комментария
  app.post("/api/add-comment", async (req, res) => {
    try {
      const {
        name,
        comment,
        movieId,
        parentId,
        "g-recaptcha-response": recaptchaToken,
      } = req.body;

      if (!name || !comment || !movieId) {
        return res.status(400).json({ error: "Неверные параметры" });
      }

      // Проверяем reCAPTCHA с secret key из .env
      if (!recaptchaToken) {
        return res
          .status(400)
          .json({ error: "Необходимо подтвердить reCAPTCHA" });
      }

      // В реальном приложении здесь была бы проверка токена с Google
      const recaptchaVerification = await verifyRecaptcha(
        recaptchaToken,
        process.env.RECAPTCHA_SECRET_KEY
      );

      if (!recaptchaVerification.success) {
        return res.status(400).json({
          error: "Проверка reCAPTCHA не удалась.",
          "error-codes": recaptchaVerification["error-codes"],
        });
      }

      // Создаем новый комментарий
      const newComment = {
        id: Date.now(),
        name: name || "Гость",
        comment,
        date: new Date().toLocaleDateString("ru-RU"),
        rating: 0,
        userVote: null,
        parentId: parentId || null,
      };

      const comments = await getCommentsForMovie(movieId);
      comments.push(newComment);
      await saveCommentsForMovie(movieId, comments);

      res.json({
        success: true,
        comment: newComment,
        commentsCount: comments.length,
      });
    } catch (error) {
      console.error("Ошибка добавления комментария:", error);
      res.status(500).json({ error: "Внутренняя ошибка сервера" });
    }
  });

  // API endpoint для получения комментариев фильма
  app.get("/api/movie-comments/:movieId", async (req, res) => {
    try {
      res.set(
        "Cache-Control",
        "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
      );
      const { movieId } = req.params;
      const comments = await getCommentsForMovie(movieId);
      res.json({
        comments,
        commentsCount: comments.length,
      });
    } catch (error) {
      console.error("Ошибка получения комментариев:", error);
      res.status(500).json({ error: "Внутренняя ошибка сервера" });
    }
  });

  // API endpoint для голосования за комментарий
  app.post("/api/vote-comment", async (req, res) => {
    try {
      res.set(
        "Cache-Control",
        "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
      );
      const { movieId, commentId, voteType, previousVote } = req.body;

      if (!movieId || !commentId) {
        return res.status(400).json({ error: "Неверные параметры" });
      }

      // voteType может быть null когда пользователь отменяет голос
      if (voteType !== "like" && voteType !== "dislike" && voteType !== null) {
        return res.status(400).json({
          error:
            "Неверные параметры: voteType должен быть like, dislike или null",
        });
      }

      const comments = await getCommentsForMovie(movieId);
      const comment = comments.find((c) => c.id === commentId);
      if (!comment) {
        return res.status(404).json({ error: "Комментарий не найден" });
      }

      if (typeof comment.rating === "undefined") comment.rating = 0;
      if (typeof comment.userVote === "undefined") comment.userVote = null;

      // Обновляем рейтинг комментария
      if (previousVote === "like") comment.rating--;
      if (previousVote === "dislike") comment.rating++;

      if (voteType === "like") comment.rating++;
      if (voteType === "dislike") comment.rating--;

      // Обновляем userVote
      comment.userVote = voteType;

      await saveCommentsForMovie(movieId, comments);

      res.json({
        success: true,
        comment: comment,
      });
    } catch (error) {
      console.error("Ошибка голосования за комментарий:", error);
      res.status(500).json({ error: "Внутренняя ошибка сервера" });
    }
  });

  // On-the-fly ресайз постеров: /img?src=/uploads/media/foo.jpg&w=360&q=70&f=webp
  // замена обработчика /img
  app.get("/img", async (req, res) => {
    try {
      const src = String(req.query.src || "");
      const w = Math.max(1, Math.min(1200, parseInt(req.query.w, 10) || 360));
      const q = Math.max(1, Math.min(95, parseInt(req.query.q, 10) || 70));
      let f = String(req.query.f || "webp").toLowerCase(); // webp|jpeg|avif

      // Только белые директории
      const uploadsDir = path.join(__dirname, "uploads");
      const assetsDir = path.join(__dirname, "assets");
      const abs = path.join(__dirname, src.replace(/^\//, ""));
      const norm = path.normalize(abs);
      const insideAllowed =
        norm.startsWith(uploadsDir + path.sep) ||
        norm.startsWith(assetsDir + path.sep);

      if (!insideAllowed) return res.status(400).send("bad-src");
      if (!fsSync.existsSync(norm)) return res.status(404).send("not found");

      // Только валидные исходные расширения
      const allowedSrcExt = new Set([
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".avif",
      ]);
      const srcExt = path.extname(norm).toLowerCase();
      if (!allowedSrcExt.has(srcExt))
        return res.status(415).send("unsupported-image");

      // Только валидные форматы вывода
      if (!["webp", "jpeg", "jpg", "avif"].includes(f)) f = "webp";

      const sharp = require("sharp");
      if (!sharpConfigured) {
        const os = require("os");
        sharp.concurrency(
          Math.max(2, Math.min(4, require("os").cpus().length))
        );
        sharp.cache({ files: 0, items: 256, memory: 128 });
        sharpConfigured = true;
      }

      let img = sharp(norm).resize({ width: w, withoutEnlargement: true });
      if (f === "avif") img = img.avif({ quality: q });
      else if (f === "jpeg" || f === "jpg")
        img = img.jpeg({ quality: q, mozjpeg: true });
      else img = img.webp({ quality: q });

      res.setHeader("Cache-Control", "public, max-age=31536000, immutable");
      res.type(f === "jpeg" ? "jpeg" : f);

      img.on("error", (err) => {
        console.error("sharp stream error:", err?.message);
        if (!res.headersSent) res.status(415).send("unsupported-image");
        try {
          res.end();
        } catch {}
      });

      img.pipe(res);
    } catch (e) {
      console.error("img handler error:", e?.message);
      res.status(500).send("img-error");
    }
  });

  // Probe external player URL (server-side) to detect "content not found" pages
  app.get("/api/probe-player", async (req, res) => {
    try {
      const { url } = req.query;
      if (!url)
        return res.status(400).json({ ok: false, error: "Missing url" });

      const u = new URL(url);
      const host = u.hostname;

      const resp = await axios.get(url, {
        timeout: 8000,
        headers: {
          "User-Agent": "Mozilla/5.0",
          Accept:
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
          Referer: BASE_URL,
        },
        validateStatus: () => true,
      });

      const status = resp.status || 0;
      const body = typeof resp.data === "string" ? resp.data : "";

      // Фразы ошибки, которые реально показывает Alloha
      const matchedSpecific =
        /К сожалению,\s*(?:запрашиваемый контент не найден|видео недоступно)/i.test(
          body
        ) ||
        /Контент не найден/i.test(body) ||
        /Приносим свои извинения за неудобства/i.test(body) ||
        /Видео запрещено к просмотру в данной стране/i.test(body) ||
        /Error\s*code:\s*[a-z0-9]+/i.test(body) ||
        /Видео не найдено/i.test(body);

      // Маркеры «живого» плеера Alloha (есть на рабочей странице, отсутствуют на чистой ошибке)
      const hasPlayerMarkers =
        /(allplay__video|allplay__player|rmp-vast|videojs|hls\.js)/i.test(body);

      const matchedTitle = /<title>\s*Ошибка!?<\/title>/i.test(body);
      const matched404 = /404\s*Not\s*Found/i.test(body);

      let looksBad;
      let matched = matchedSpecific;

      if (/stloadi\.live/i.test(host)) {
        // Для Alloha считаем «плохо» только если есть явный текст ошибки и нет маркеров плеера
        looksBad = matchedSpecific && !hasPlayerMarkers;
        matched = matchedSpecific && !hasPlayerMarkers;
      } else if (/(^|\.)atomics\.ws$/i.test(host)) {
        // Для Atomics считаем «плохо» только при явном тексте ошибки (игнорируем 4xx)
        looksBad = matchedSpecific;
        matched = matchedSpecific;
      } else {
        looksBad =
          status >= 400 || matchedSpecific || matchedTitle || matched404;
      }

      const debug = String(req.query.debug || "") === "1";
      const sample = body.slice(0, 800);

      if (debug) {
        console.log("[probe]", { host, status, matched, looksBad });
        console.log("[probe-full]", {
          host,
          status,
          matched,
          looksBad,
          sample: sample.replace(/\n/g, " "),
        });
      }

      if (debug) {
        return res.json({
          ok: !looksBad,
          status,
          matched,
          host,
          looksBad,
          sample,
        });
      }
      res.json({ ok: !looksBad, status, matched, host });
    } catch (e) {
      const debug = String(req.query.debug || "") === "1";

      // Попробуем вытащить данные из axios-ошибки (если они есть)
      const host = (() => {
        try {
          return new URL(String(req.query.url || "")).hostname;
        } catch {
          return null;
        }
      })();
      const status = e?.response?.status || 0;
      const body = typeof e?.response?.data === "string" ? e.response.data : "";
      const sample = body.slice(0, 800);

      console.error("[probe-error]", { host, status, message: e?.message });
      if (debug) {
        return res.json({
          ok: false,
          host,
          status,
          matched: false,
          looksBad: true,
          sample,
          error: e?.message || "request-failed",
        });
      }
      return res.json({ ok: false, error: "request-failed" });
    }
  });
  // server.js — рядом с /api/kd-loader.js
  app.get("/api/cdnvh-playerui.js", async (req, res) => {
    try {
      const upstream =
        "https://stage.player.cdnvideohub.com/static/playerui.js";
      const resp = await axios.get(upstream, {
        timeout: 10000,
        headers: {
          "User-Agent": "Mozilla/5.0",
          Accept: "application/javascript,text/javascript,*/*;q=0.1",
          Referer: BASE_URL,
        },
        responseType: "text",
        validateStatus: () => true,
      });
      if (resp.status >= 400 || !resp.data) {
        return res
          .status(502)
          .type("application/javascript")
          .send("// cdnvh proxy: upstream failed");
      }
      res.set("Content-Type", "application/javascript; charset=utf-8");
      res.set("Cache-Control", "public, max-age=2592000, immutable"); // 30d
      res.send(resp.data);
    } catch (e) {
      res
        .status(502)
        .type("application/javascript")
        .send("// cdnvh proxy: request failed");
    }
  });

  app.get("/api/cdnvh-umd.js", async (req, res) => {
    try {
      const upstream =
        "https://player.cdnvideohub.com/s2/stable/video-player.umd.js";
      const resp = await axios.get(upstream, {
        timeout: 15000,
        headers: {
          "User-Agent": "Mozilla/5.0",
          Accept: "application/javascript,text/javascript,*/*;q=0.1",
          Referer: BASE_URL,
        },
        responseType: "text",
        validateStatus: () => true,
      });
      if (resp.status >= 400 || !resp.data) {
        return res
          .status(502)
          .type("application/javascript")
          .send("// cdnvh umd proxy: upstream failed");
      }
      res.set("Content-Type", "application/javascript; charset=utf-8");
      // 30 days. You can use 1y + immutable if you always bump the path when upstream changes.
      res.set("Cache-Control", "public, max-age=2592000, immutable");
      res.send(resp.data);
    } catch (e) {
      res
        .status(502)
        .type("application/javascript")
        .send("// cdnvh umd proxy: request failed");
    }
  });

  // Прокси для загрузчика Kodik, чтобы обойти блокировки/AdBlock
  app.get("/api/kd-loader.js", async (req, res) => {
    try {
      const upstream = "https://kodik-add.com/add-players.min.js";
      const resp = await axios.get(upstream, {
        timeout: 10000,
        headers: {
          "User-Agent": "Mozilla/5.0",
          Accept: "application/javascript,text/javascript,*/*;q=0.1",
          Referer: BASE_URL,
        },
        responseType: "text",
        validateStatus: () => true,
      });
      if (resp.status >= 400 || !resp.data) {
        return res
          .status(502)
          .type("application/javascript")
          .send("// kd proxy: upstream failed");
      }
      res.set("Content-Type", "application/javascript; charset=utf-8");
      res.set("Cache-Control", "public, max-age=2592000, immutable");
      res.send(resp.data);
    } catch (e) {
      res
        .status(502)
        .type("application/javascript")
        .send("// kd proxy: request failed");
    }
  });

  app.get("/api/asset-loader.js", async (req, res) => {
    try {
      const upstream = "https://california1955.nl/s2/asset.loader.js";
      const resp = await axios.get(upstream, {
        timeout: 10000,
        responseType: "text",
        validateStatus: () => true,
      });
      if (resp.status >= 400 || !resp.data) {
        return res
          .status(502)
          .type("application/javascript")
          .send("// asset proxy failed");
      }
      res.set("Content-Type", "application/javascript; charset=utf-8");
      res.set("Cache-Control", "public, max-age=2592000, immutable");
      res.send(resp.data);
    } catch {
      res
        .status(502)
        .type("application/javascript")
        .send("// asset proxy: request failed");
    }
  });

  // /api/cdnvh-esm.js — пробуем ESM, иначе UMD
  app.get("/api/cdnvh-esm.js", async (req, res) => {
    const tryUrls = [
      "https://player.cdnvideohub.com/s2/stable/video-player.es.js",
      "https://player.cdnvideohub.com/s2/stable/video-player.esm.js",
      "https://player.cdnvideohub.com/s2/stable/video-player.module.js",
    ];
    try {
      for (const u of tryUrls) {
        const r = await axios.get(u, {
          timeout: 12000,
          responseType: "text",
          validateStatus: () => true,
        });
        if (r.status < 400 && r.data) {
          res.set("Content-Type", "application/javascript; charset=utf-8");
          res.set("Cache-Control", "public, max-age=2592000, immutable");
          return res.send(r.data);
        }
      }
      // fallback: UMD
      const r = await axios.get(
        "https://player.cdnvideohub.com/s2/stable/video-player.umd.js",
        {
          timeout: 15000,
          responseType: "text",
          validateStatus: () => true,
        }
      );
      res.set("Content-Type", "application/javascript; charset=utf-8");
      res.set("Cache-Control", "public, max-age=2592000, immutable");
      res.send(r.data || "");
    } catch {
      res
        .status(502)
        .type("application/javascript")
        .send("// cdnvh esm proxy: request failed");
    }
  });

  // SEO: robots.txt
  //   app.get("/robots.txt", (req, res) => {
  //     res.type("text/plain").send(
  //       `User-agent: *
  // Allow: /
  // Disallow: /api/
  // Sitemap: ${BASE_URL}/sitemap.xml
  // `
  //     );
  //   });

  app.get("/robots.txt", (req, res) => {
    const block = process.env.BLOCK_INDEXING === "true";
    res.type("text/plain").send(
      block
        ? `User-agent: *
Disallow: /`
        : `User-agent: *
Allow: /
Disallow: /api/
Sitemap: ${BASE_URL}/sitemap.xml
`
    );
  });

  app.get("/favicon.ico", (req, res) => {
    // res.sendFile(path.join(__dirname, "assets/ProsmotrZone_site/images/favicon.ico"));
    res.set("Cache-Control", "public, max-age=0, must-revalidate");
    res.type("image/x-icon");
    res.sendFile(
      path.join(__dirname, "assets/ProsmotrZone_site/images/favicon.ico")
    );
  });

  // SEO: sitemap.xml
  app.get("/sitemap.xml", async (req, res) => {
    try {
      const data = await readData();
      const movies = (data?.movies || []).filter(
        (m) => m.id !== "index" && !isHidden(m)
      );
      const siteLastmodDate = new Date(lastModifiedTime || Date.now());
      const getMovieLastmod = (m) => {
        const today = new Date();
        const min = new Date("1990-01-01");
        let d =
          parseRussianPremiere(m.premiere) ||
          (Number(m.year) >= 1900 ? new Date(`${m.year}-01-01`) : null);

        if (!d || isNaN(d.getTime())) d = siteLastmodDate;
        if (d < min) d = siteLastmodDate;
        if (d > today) d = today;
        if (d < siteLastmodDate) d = siteLastmodDate; // не старее обновления данных
        return d.toISOString().split("T")[0];
      };

      const siteLastmod = new Date(lastModifiedTime || Date.now())
        .toISOString()
        .split("T")[0];

      const urls = [
        { loc: `${BASE_URL}/`, priority: "1.0", lastmod: siteLastmod },
        { loc: `${BASE_URL}/filmy`, priority: "0.8", lastmod: siteLastmod },
        { loc: `${BASE_URL}/serialy`, priority: "0.8", lastmod: siteLastmod },
        { loc: `${BASE_URL}/multfilmy`, priority: "0.8", lastmod: siteLastmod },
        { loc: `${BASE_URL}/anime`, priority: "0.8", lastmod: siteLastmod },
        {
          loc: `${BASE_URL}/top-all-time`,
          priority: "0.6",
          lastmod: siteLastmod,
        },
        {
          loc: `${BASE_URL}/serialy?special=doramas`,
          priority: "0.5",
          lastmod: siteLastmod,
        },
        {
          loc: `${BASE_URL}/serialy?special=turkish`,
          priority: "0.5",
          lastmod: siteLastmod,
        },
      ].concat(
        movies.map((m) => ({
          loc: `${BASE_URL}/${m.category}/${m.id}`,
          priority: "0.6",
          lastmod: getMovieLastmod(m),
        }))
      );

      const xml = `<?xml version="1.0" encoding="UTF-8"?>
      <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      ${urls
        .map(
          (u) => `  <url>
          <loc>${u.loc}</loc>
          <lastmod>${u.lastmod}</lastmod>
          <changefreq>weekly</changefreq>
          <priority>${u.priority}</priority>
        </url>`
        )
        .join("\n")}
      </urlset>`;
      res.type("application/xml").send(xml);
    } catch (e) {
      console.error("Ошибка sitemap:", e);
      res.status(500).send("Sitemap generation error");
    }
  });

  function stripTags(html) {
    return String(html || "")
      .replace(/<[^>]*>/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }
  function truncate(s, n = 300) {
    s = String(s || "");
    return s.length <= n ? s : s.slice(0, n).replace(/\s+\S*$/, "") + "…";
  }
  function computeSeo(url, data, BASE_URL) {
    const u = new URL(BASE_URL + url);
    const path = u.pathname.replace(/\/+$/, "") || "/";
    const movies = data?.movies || [];
    const categories = data?.categories || {};

    // ВАЖНО: существующий файл в корневой папке assets
    const defaultOgImage = `${BASE_URL}/assets/ProsmotrZone_site/images/NewLogo.webp`;

    const seo = {
      title:
        "ProsmotrZone - смотреть фильмы и сериалы в HD качестве онлайн бесплатно",
      description:
        "На ProsmotrZone вас ждут новые фильмы, сериалы и аниме онлайн. Смотрите премьеры 2025 года, классику, рейтинговые хиты и новинки. Здесь вы можете смотреть без регистрации бесплатно в HD (720p, 1080p) без лишней рекламы. Удобный поиск и фильтры по жанрам, актёрам, годам и другим параметрам. Можете смотреть с любого устройства в любое время дня.",
      canonical: BASE_URL + "/",
      ogImage: defaultOgImage,
      robots: "index,follow",
      ldJson: null,
      status: 200,
      ogType: "website",
    };

    // Главная
    if (path === "/") {
      // Структурированная разметка для поиска по сайту
      seo.ldJson = {
        website: {
          "@context": "https://schema.org",
          "@type": "WebSite",
          url: `${BASE_URL}/`,
          name: "ProsmotrZone",
          potentialAction: {
            "@type": "SearchAction",
            target: `${BASE_URL}/?q={search_term_string}`,
            "query-input": "required name=search_term_string",
          },
        },
      };
      return seo;
    }

    // Топ
    if (path === "/top-all-time") {
      const t = (u.searchParams.get("type") || "all").toLowerCase();
      const label =
        {
          all: "фильмы и сериалы",
          filmy: "фильмы",
          serialy: "сериалы",
          multfilmy: "мультфильмы",
          anime: "аниме",
          doramas: "дорамы",
          turkish: "турецкие сериалы",
        }[t] || "фильмы и сериалы";

      seo.title =
        t === "all"
          ? "Топ всех фильмов и сериалов — ProsmotrZone"
          : `Топ: ${label} — ProsmotrZone`;

      seo.description =
        "Лучшие фильмы и сериалы по рейтингу IMDb и Кинопоиск на ProsmotrZone. Выбирайте и смотрите онлайн бесплатно в HD.";
      seo.canonical = `${BASE_URL}/top-all-time`; // фиксированный canonical
      return seo;
    }
    if (path === "/novinki") {
      const nowY = new Date().getFullYear();
      const y =
        parseInt(u.searchParams.get("year") || String(nowY), 10) || nowY;
      const cat = (u.searchParams.get("category") || "all").toLowerCase();
      const label =
        {
          all: "фильмы, сериалы, мультфильмы и аниме",
          filmy: "фильмы",
          serialy: "сериалы",
          multfilmy: "мультфильмы",
          anime: "аниме",
          doramas: "дорамы",
          turkish: "турецкие сериалы",
        }[cat] || "фильмы, сериалы, мультфильмы и аниме";

      seo.title =
        cat === "all"
          ? `Новинки ${y} — ProsmotrZone`
          : `Новинки ${y}: ${label} — ProsmotrZone`;

      seo.description = `Свежие новинки ${y} года: ${label}. Смотрите онлайн в хорошем качестве на ProsmotrZone.`;
      seo.canonical = `${BASE_URL}/novinki`; // фиксированный canonical
      return seo;
    }

    const knownCats = ["filmy", "serialy", "multfilmy", "anime"];
    const parts = path.split("/").filter(Boolean);

    // Категории: /filmy, /serialy, /multfilmy, /anime (+ query)
    if (knownCats.includes(path.slice(1))) {
      const cat = path.slice(1);
      const sp = u.searchParams;
      const year = sp.get("year") || "";
      const genre = sp.get("genre") || "";
      const country = sp.get("country") || "";
      const translation = sp.get("translation") || "";
      const actor = sp.get("actor") || "";
      const special = sp.get("special") || "";
      const pageNum = parseInt(sp.get("page") || "1", 10) || 1;

      const forms = {
        filmy: {
          nom: "Фильмы",
          gen: "фильмов",
          lower: "фильмы",
          sing: "фильм",
        },
        serialy: {
          nom: "Сериалы",
          gen: "сериалов",
          lower: "сериалы",
          sing: "сериал",
        },
        multfilmy: {
          nom: "Мультфильмы",
          gen: "мультфильмов",
          lower: "мультфильмы",
          sing: "мультфильм",
        },
        anime: { nom: "Аниме", gen: "аниме", lower: "аниме", sing: "аниме" },
      };
      const fallback = categories[cat] || "Контент";
      const f = forms[cat] || {
        nom: fallback,
        gen: fallback.toLowerCase(),
        lower: fallback.toLowerCase(),
        sing: fallback.toLowerCase(),
      };

      // Квалификаторы
      const qual = [];
      if (genre) qual.push(`жанра ${genre}`);
      if (country) qual.push(`страны ${country}`);
      if (year) qual.push(`за ${year} год`);
      if (translation) qual.push(`в переводе ${translation}`);

      let listSubjectGen = f.gen; // "фильмов"
      let browseSubjectNomLower = f.lower; // "фильмы"
      if (special === "doramas") {
        listSubjectGen = "дорам";
        browseSubjectNomLower = "дорамы";
      } else if (special === "turkish") {
        listSubjectGen = "турецких сериалов";
        browseSubjectNomLower = "турецкие сериалы";
      }
      if (actor) {
        qual.unshift(`с ${actor}`);
      }
      const qualStr = qual.length ? ` ${qual.join(", ")}` : "";

      seo.title = `Список всех ${listSubjectGen}${qualStr} смотреть онлайн бесплатно в хорошем качестве на ProsmotrZone`;
      if (pageNum > 1) {
        seo.title += ` — страница ${pageNum}`;
      }
      seo.description = `Выбирайте для просмотра ${browseSubjectNomLower}${qualStr} с помощью удобных фильтров и смотрите в HD качестве без регистрации онлайн на ProsmotrZone.`;

      // canonical — нормализуем: убираем дефолтные page/limit/sort
      const usp = new URLSearchParams(u.search);
      if ((usp.get("page") || "1") === "1") usp.delete("page");
      if ((usp.get("limit") || "24") === "24") usp.delete("limit");
      if ((usp.get("sort") || "year") === "year") usp.delete("sort");
      const qs = usp.toString();
      seo.canonical = `${BASE_URL}/${cat}${qs ? `?${qs}` : ""}`;

      // Для prev/next и определения пустых выдач — строим feed
      const feedParams = {
        name: cat,
        page: pageNum,
        limit: Math.max(
          1,
          Math.min(200, parseInt(sp.get("limit") || "24", 10))
        ),
        sort: sp.get("sort") || "year",
        year,
        genre,
        country,
        translation,
        actor,
        special,
        home: false,
      };
      const feed = buildCategoryFeed(data, feedParams);

      // rel prev/next
      const mkAbsUrl = (p) => {
        const usp = new URLSearchParams(u.search);
        usp.set("page", String(p));
        // (опционально) можно тоже убирать дефолтные limit/sort:
        if ((usp.get("limit") || "24") === "24") usp.delete("limit");
        if ((usp.get("sort") || "year") === "year") usp.delete("sort");
        const qs = usp.toString();
        return `${BASE_URL}/${cat}${qs ? `?${qs}` : ""}`;
      };
      if (feed.page > 1) seo.prevUrl = mkAbsUrl(feed.page - 1);
      if (feed.page < feed.totalPages) seo.nextUrl = mkAbsUrl(feed.page + 1);

      // Пустые выдачи — noindex,follow
      if (feed.total === 0) {
        seo.robots = "noindex,follow";
      }
      // после const feed = buildCategoryFeed(data, feedParams);
      if (feed.page > feed.totalPages) {
        seo.robots = "noindex,follow";
      }
      const itemList = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        itemListElement: feed.items.map((it, idx) => ({
          "@type": "ListItem",
          position: idx + 1 + (feed.page - 1) * feed.limit,
          url: `${BASE_URL}/${it.category}/${it.id}`,
          name: it.title,
        })),
      };
      seo.ldJson = { ...(seo.ldJson || {}), list: itemList };
      return seo;
    }

    // Movie: /:category/:id
    if (parts.length === 2) {
      const [cat, id] = parts;
      const m = movies.find((x) => x.id === id);
      if (!m || isHidden(m)) {
        seo.title = "Страница не найдена — ProsmotrZone";
        seo.description = "Страница не найдена.";
        seo.canonical = `${BASE_URL}${path}`;
        seo.robots = "noindex,follow";
        seo.status = 404;
        return seo;
      }

      seo.ogType = "video.movie";
      const year = m.year ? ` (${m.year})` : "";
      seo.title = `${m.title}${year} смотреть онлайн бесплатно в хорошем качестве`;

      const isSerial =
        m.category === "serialy" ||
        m.category === "serials" ||
        m.category === "anime" ||
        m.category === "animes" ||
        !!m.season ||
        !!m.episode;

      const typeLabel =
        m.category === "filmy"
          ? "фильм"
          : m.category === "serialy" || m.category === "serials"
          ? "сериал"
          : m.category === "anime" || m.category === "animes"
          ? "аниме"
          : m.season || m.episode
          ? "мультсериал"
          : "мультфильм";

      const metaParts = [];
      if (m.year) metaParts.push(String(m.year));
      const se = [];
      if (m.season) {
        const s = String(m.season).trim();
        se.push(/сезон/i.test(s) ? s : `${s} сезон`);
      }
      if (m.episode) {
        const e = String(m.episode).trim();
        se.push(/сер(ия|ии)/i.test(e) ? e : `${e} серия`);
      }
      if (se.length) metaParts.push(se.join(" "));
      const details = metaParts.length ? ` (${metaParts.join(", ")})` : "";

      const synopsis = stripTags(m.description);
      const synopsisShort = truncate(synopsis, 200);
      const metaDesc = isSerial
        ? `Смотреть ${typeLabel} ${m.title} все серии подряд${details}. Описание: ${synopsisShort}`
        : `Смотреть ${typeLabel} ${m.title}${details} онлайн в отличном качестве с русской озвучкой. Описание: ${synopsisShort}`;

      seo.description = metaDesc;
      seo.canonical = `${BASE_URL}/${m.category}/${m.id}`;

      const posterAbs = m.image
        ? m.image.startsWith("http")
          ? m.image
          : `${BASE_URL}/${
              m.image.startsWith("/") ? m.image.slice(1) : m.image
            }`
        : null;
      seo.ogImage = posterAbs || defaultOgImage;

      const ratingRaw = m.imdbRating || m.kpRating;
      const ratingNum = parseFloat(String(ratingRaw || "").replace(",", "."));
      const ldDesc = truncate(synopsis, 300);

      // Более богатый JSON-LD
      const baseType = isSerial ? "TVSeries" : "Movie";
      const ld = {
        "@context": "https://schema.org",
        "@type": baseType,
        name: m.title,
        datePublished: m.year ? String(m.year) : undefined,
        image: posterAbs || defaultOgImage,
        description: ldDesc,
        genre: Array.isArray(m.genres) ? m.genres.filter(Boolean) : undefined,
        actor: Array.isArray(m.actors)
          ? m.actors.slice(0, 10).map((name) => ({ "@type": "Person", name }))
          : undefined,
        director: m.director
          ? [{ "@type": "Person", name: m.director }]
          : undefined,
        trailer: m.trailer
          ? [{ "@type": "VideoObject", url: m.trailer }]
          : undefined,
        aggregateRating:
          Number.isFinite(ratingNum) && ratingNum > 0
            ? {
                "@type": "AggregateRating",
                ratingValue: ratingNum.toFixed(1),
                bestRating: "10",
                worstRating: "0",
              }
            : undefined,
      };
      if (m.season || m.episode) {
        ld.partOfSeries = { "@type": "TVSeries", name: m.title };
      }
      const breadcrumbsLd = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        itemListElement: [
          {
            "@type": "ListItem",
            position: 1,
            name: "Главная",
            item: `${BASE_URL}/`,
          },
          {
            "@type": "ListItem",
            position: 2,
            name: categories?.[m.category] || "Категория",
            item: `${BASE_URL}/${m.category}`,
          },
          {
            "@type": "ListItem",
            position: 3,
            name: m.title,
            item: `${BASE_URL}/${m.category}/${m.id}`,
          },
        ],
      };
      seo.ldJson = { movie: ld, breadcrumbs: breadcrumbsLd };
      return seo;
    }

    // Любая другая вложенность в известных категориях → 404
    if (parts.length > 0 && knownCats.includes(parts[0])) {
      seo.title = "Страница не найдена — ProsmotrZone";
      seo.description = "Страница не найдена.";
      seo.canonical = `${BASE_URL}${path}`;
      seo.robots = "noindex,follow";
      seo.status = 404;
      return seo;
    }

    // Неизвестный путь → 404
    seo.title = "Страница не найдена — ProsmotrZone";
    seo.description = "Страница не найдена.";
    seo.canonical = `${BASE_URL}${path}`;
    seo.robots = "noindex,follow";
    seo.status = 404;
    return seo;
  }

  function isBot(ua = "") {
    ua = String(ua).toLowerCase();
    return /(bot|crawl|spider|slurp|bing|facebook|telegram|whatsapp|vkshare|preview|embed|fetch|validator|lighthouse)/i.test(
      ua
    );
  }
  function parseRoute(url) {
    const p = (url.split("?")[0] || "/").replace(/\/+$/, "") || "/";
    const parts = p.split("/").filter(Boolean);
    if (p === "/") return { type: "home" };
    if (p === "/top-all-time") return { type: "tops" };
    if (p === "/novinki") return { type: "novinki" };
    if (
      ["filmy", "serialy", "multfilmy", "anime"].includes(parts[0]) &&
      parts.length === 1
    ) {
      return { type: "category", category: parts[0] };
    }
    if (parts.length === 2)
      return { type: "movie", category: parts[0], id: parts[1] };
    return { type: "unknown" };
  }

  function injectSeo(html, seo = {}) {
    const escapeAttr = (value = "") =>
      String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/"/g, "&quot;")
        .replace(/</g, "&lt;");

    const escapeText = (value = "") =>
      String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    const serializeJsonLd = (payload) =>
      JSON.stringify(payload ?? {}).replace(/</g, "\\u003c");

    const upsert = (pattern, tag) => {
      if (pattern.test(html)) {
        html = html.replace(pattern, tag);
      } else {
        html = html.replace("</head>", `  ${tag}\n</head>`);
      }
    };

    const titleText = escapeText(seo.title || "");
    if (titleText) {
      html = html.replace(
        /<title>[\s\S]*?<\/title>/i,
        `<title>${titleText}</title>`
      );
    }

    const descriptionAttr = escapeAttr(seo.description ?? "");
    upsert(
      /<meta\s+name=["']description["'][^>]*>/i,
      `<meta name="description" content="${descriptionAttr}">`
    );

    if (seo.robots !== undefined && seo.robots !== null) {
      const robotsAttr = escapeAttr(seo.robots);
      upsert(
        /<meta\s+name=["']robots["'][^>]*>/i,
        `<meta name="robots" content="${robotsAttr}">`
      );
    }

    if (seo.canonical) {
      const canonicalAttr = escapeAttr(seo.canonical);
      upsert(
        /<link\s+rel=["']canonical["'][^>]*>/i,
        `<link rel="canonical" href="${canonicalAttr}">`
      );
    }

    // Новые prev/next ссылки
    if (seo.prevUrl) {
      upsert(
        /<link\s+rel=["']prev["'][^>]*>/i,
        `<link rel="prev" href="${escapeAttr(seo.prevUrl)}">`
      );
    }
    if (seo.nextUrl) {
      upsert(
        /<link\s+rel=["']next["'][^>]*>/i,
        `<link rel="next" href="${escapeAttr(seo.nextUrl)}">`
      );
    }

    const ogPairs = [
      ["og:type", seo.ogType || "website"],
      ["og:site_name", "ProsmotrZone"],
      ["og:locale", "ru_RU"],
      ["og:title", seo.title],
      ["og:description", seo.description],
      ["og:url", seo.canonical],
    ];
    if (seo.ogImage) ogPairs.push(["og:image", seo.ogImage]);

    for (const [prop, value] of ogPairs) {
      if (value === undefined || value === null || value === "") continue;
      const escaped = escapeAttr(value);
      upsert(
        new RegExp(`<meta\\s+property=["']${prop}["'][^>]*>`, "i"),
        `<meta property="${prop}" content="${escaped}">`
      );
    }

    const twPairs = [
      ["twitter:card", seo.ogImage ? "summary_large_image" : "summary"],
      ["twitter:title", seo.title],
      ["twitter:description", seo.description],
    ];
    if (seo.ogImage) twPairs.push(["twitter:image", seo.ogImage]);

    for (const [name, value] of twPairs) {
      if (value === undefined || value === null || value === "") continue;
      const escaped = escapeAttr(value);
      upsert(
        new RegExp(`<meta\\s+name=["']${name}["'][^>]*>`, "i"),
        `<meta name="${name}" content="${escaped}">`
      );
    }

    if (seo.ldJson) {
      const entries = Array.isArray(seo.ldJson)
        ? seo.ldJson
        : typeof seo.ldJson === "object"
        ? Object.entries(seo.ldJson)
        : [["ldjson", JSON.parse(seo.ldJson)]];
      for (const [id, payload] of entries) {
        const tag = `<script type="application/ld+json" data-id="${escapeAttr(
          id
        )}">${serializeJsonLd(payload)}</script>`;
        const re = new RegExp(
          `<script\\s+type=["']application/ld\\+json["'][^>]*data-id=["']${id}["'][^>]*>[\\s\\S]*?<\\/script>`,
          "i"
        );
        if (re.test(html)) {
          html = html.replace(re, tag);
        } else {
          html = html.replace("</head>", `  ${tag}\n</head>`);
        }
      }
    }

    return html;
  }
  app.get("/health", (req, res) => res.type("text/plain").send("ok"));
  // SSR catch-all handler (должен быть последним)
  app.use("*", async (req, res, next) => {
    const url = req.originalUrl;
    const accept = String(req.headers.accept || "");

    // Отдаем SSR только для HTML-запросов
    const pathname = req.originalUrl.split("?")[0] || "/";
    const isAsset =
      pathname.startsWith("/.well-known/") ||
      /\.(json|txt|xml|ico|png|jpg|jpeg|gif|webp|avif|svg|js|css|map|woff2?|ttf)$/i.test(
        pathname
      );
    const isHtmlLike = req.method === "GET" && !isAsset;
    if (!isHtmlLike) return next();

    // Пропускаем технич. пути и ассеты к vite/static
    if (
      url.startsWith("/.well-known/") ||
      /\.(json|txt|xml|ico|png|jpg|jpeg|gif|webp|avif|svg|js|css|map)$/i.test(
        url
      )
    ) {
      return next();
    }

    try {
      let html;

      if (!isProduction) {
        // Development режим
        let devTemplate = await fs.readFile(
          path.resolve("index.html"),
          "utf-8"
        );

        // ВАЖНО: фикс — трансформим как '/', а не как текущий .json/.ico URL
        devTemplate = await vite.transformIndexHtml("/", devTemplate);

        const { render: devRender } = await vite.ssrLoadModule(
          "/src/entry-server.js"
        );
        // Production режим
        const data = await readData();

        const ua = String(req.headers["user-agent"] || "");
        const routeInfo = parseRoute(url);
        const initialState = {};
        const urlObj = new URL(BASE_URL + url);

        // быстрый hit для людей (не боты)
        if (!isBot(ua)) {
          const hit = getSsrFromCache(url);
          if (hit) {
            return res
              .status(hit.status)
              .set({ "Content-Type": "text/html" })
              .end(hit.html);
          }
        }

        if (routeInfo.type === "home") {
          initialState.homeFeed = getHomeFeed(data);
        } else if (routeInfo.type === "tops") {
          const t = urlObj.searchParams.get("type") || "all";
          initialState.topFeed = {
            type: t,
            limit: 24,
            offset: 0,
            data: getTopFeedPaged(data, { limit: 24, offset: 0, type: t }),
          };
        } else if (routeInfo.type === "category") {
          const params = {
            name: routeInfo.category,
            page: urlObj.searchParams.get("page") || 1,
            limit: urlObj.searchParams.get("limit") || 24,
            sort: urlObj.searchParams.get("sort") || "year",
            year: urlObj.searchParams.get("year") || "",
            genre: urlObj.searchParams.get("genre") || "",
            country: urlObj.searchParams.get("country") || "",
            translation: urlObj.searchParams.get("translation") || "",
            actor: urlObj.searchParams.get("actor") || "",
            special: urlObj.searchParams.get("special") || "",
          };
          initialState.categoryFeed = {
            slug: routeInfo.category,
            feed: buildCategoryFeed(data, params),
            params,
          };
        } else if (routeInfo.type === "movie") {
          await readRelatedMap(); // добавить
          const payload = buildMoviePayload(data, routeInfo.id);
          if (payload) {
            initialState.moviePayload = payload;
          } else {
            res.status(404);
          }
        } else if (routeInfo.type === "unknown") {
          res.status(404);
        }

        // Готовим HTML приложения
        const { html: appHtml } = await devRender(url, initialState);

        // Формируем облегчённые инлайновые данные (только для людей)
        const scripts = [];
        if (!isBot(ua)) {
          if (initialState.homeFeed) {
            scripts.push(
              `window.__HOME_FEED__=${JSON.stringify(
                initialState.homeFeed
              ).replace(/</g, "\\u003c")}`
            );
          }
          if (initialState.topFeed) {
            const j = {
              items: initialState.topFeed.data.items,
              total: initialState.topFeed.data.total,
              limit: initialState.topFeed.limit,
              offset: initialState.topFeed.offset,
              type: initialState.topFeed.type,
            };
            scripts.push(
              `window.__TOP_FEED__=${JSON.stringify(j).replace(
                /</g,
                "\\u003c"
              )}`
            );
          }
          if (initialState.categoryFeed) {
            const cfg = initialState.categoryFeed;
            scripts.push(
              `window.__CATEGORY_FEED__=window.__CATEGORY_FEED__||{};window.__CATEGORY_FEED__[${JSON.stringify(
                cfg.slug
              )}]=${JSON.stringify(cfg.feed).replace(/</g, "\\u003c")}`
            );
          }
          if (initialState.moviePayload) {
            scripts.push(
              `window.__MOVIE_PAYLOAD__=${JSON.stringify(
                initialState.moviePayload
              ).replace(/</g, "\\u003c")}`
            );
          }
        }
        const stateScript = scripts.length
          ? `<script>${scripts.join(";")}</script>`
          : "";

        // Сборка HTML (как было)
        html = devTemplate
          .replace(`<!--preload-links-->`, "")
          .replace(`<!--ssr-outlet-->`, appHtml)
          .replace(`<!--initial-state-->`, stateScript);

        // SEO-инъекция и 404
        const seo = computeSeo(url, data, BASE_URL);
        if (process.env.FORCE_NOINDEX === "1") seo.robots = "noindex, nofollow";
        if (seo.robots && /noindex/i.test(seo.robots)) {
          res.set("X-Robots-Tag", seo.robots);
        }
        html = injectSeo(html, seo);
        html = upsertPreconnects(html, [
          "https://player.cdnvideohub.com",
          "https://plapi.cdnvideohub.com",
          "https://california1955.nl",
          "https://pleer-laguna.ru",
          "https://polygamist-as.stloadi.live",
          "https://kodik-add.com",
          "https://kodikapi.com",
        ]);
        if (seo.status === 404) res.status(404);
      } else {
        // Production режим
        const data = await readData();

        const ua = String(req.headers["user-agent"] || "");
        const routeInfo = parseRoute(url);
        const initialState = {};
        const urlObj = new URL(BASE_URL + url);

        if (routeInfo.type === "home") {
          initialState.homeFeed = getHomeFeed(data);
        } else if (routeInfo.type === "tops") {
          const t = urlObj.searchParams.get("type") || "all";
          initialState.topFeed = {
            type: t,
            limit: 24,
            offset: 0,
            data: getTopFeedPaged(data, { limit: 24, offset: 0, type: t }),
          };
        } else if (routeInfo.type === "category") {
          const params = {
            name: routeInfo.category,
            page: urlObj.searchParams.get("page") || 1,
            limit: urlObj.searchParams.get("limit") || 24,
            sort: urlObj.searchParams.get("sort") || "year",
            year: urlObj.searchParams.get("year") || "",
            genre: urlObj.searchParams.get("genre") || "",
            country: urlObj.searchParams.get("country") || "",
            translation: urlObj.searchParams.get("translation") || "",
            actor: urlObj.searchParams.get("actor") || "",
            special: urlObj.searchParams.get("special") || "",
          };
          initialState.categoryFeed = {
            slug: routeInfo.category,
            feed: buildCategoryFeed(data, params),
            params,
          };
        } else if (routeInfo.type === "movie") {
          await readRelatedMap(); // добавить
          const payload = buildMoviePayload(data, routeInfo.id);
          if (payload) {
            initialState.moviePayload = payload;
          } else {
            res.status(404);
          }
        } else if (routeInfo.type === "unknown") {
          res.status(404);
        }

        const { html: appHtml, ctx } = await render(url, initialState);
        const manifest = JSON.parse(
          await fs.readFile("dist/client/.vite/ssr-manifest.json", "utf-8")
        );
        const preload = renderPreloadLinks(ctx.modules, manifest);

        const scripts = [];
        if (initialState.homeFeed) {
          scripts.push(
            `window.__HOME_FEED__=${JSON.stringify(
              initialState.homeFeed
            ).replace(/</g, "\\u003c")}`
          );
        }
        if (initialState.topFeed) {
          const j = {
            items: initialState.topFeed.data.items,
            total: initialState.topFeed.data.total,
            limit: initialState.topFeed.limit,
            offset: initialState.topFeed.offset,
            type: initialState.topFeed.type,
          };
          scripts.push(
            `window.__TOP_FEED__=${JSON.stringify(j).replace(/</g, "\\u003c")}`
          );
        }
        if (initialState.categoryFeed) {
          const cfg = initialState.categoryFeed;
          scripts.push(
            `window.__CATEGORY_FEED__=window.__CATEGORY_FEED__||{};window.__CATEGORY_FEED__[${JSON.stringify(
              cfg.slug
            )}]=${JSON.stringify(cfg.feed).replace(/</g, "\\u003c")}`
          );
        }
        if (initialState.moviePayload) {
          scripts.push(
            `window.__MOVIE_PAYLOAD__=${JSON.stringify(
              initialState.moviePayload
            ).replace(/</g, "\\u003c")}`
          );
        }
        const stateScript = scripts.length
          ? `<script>${scripts.join(";")}</script>`
          : "";

        let htmlBase = injectPreloadLinks(template, preload)
          .replace("<!--ssr-outlet-->", appHtml)
          .replace("<!--initial-state-->", stateScript);

        try {
          const critters = new Critters({
            path: require("path").resolve("dist/client"),
            publicPath: "/",
            preload: "swap", // остатки CSS грузим неблокирующе
            pruneSource: true, // удаляем из <link rel="stylesheet"> то, что инлайнено
            reduceInlineStyles: true,
          });
          html = await critters.process(htmlBase);
        } catch (e) {
          // Фолбэк: ваш текущий неблокирующий конвертер
          html = transformStylesheetsToPreload(htmlBase);
        }

        const seo = computeSeo(url, data, BASE_URL);
        if (seo.robots && /noindex/i.test(seo.robots)) {
          res.set("X-Robots-Tag", seo.robots);
        }
        html = injectSeo(html, seo);
        html = upsertPreconnects(html, [
          "https://player.cdnvideohub.com",
          "https://plapi.cdnvideohub.com",
          "https://california1955.nl",
          "https://pleer-laguna.ru",
          "https://polygamist-as.stloadi.live",
          "https://kodik-add.com",
          "https://kodikapi.com",
        ]);

        const AHREFS = process.env.AHREFS_VERIFY_TOKEN;
        if (
          AHREFS &&
          !/<meta\s+name=["']ahrefs-site-verification["'][^>]*>/i.test(html)
        ) {
          html = html.replace(
            "</head>",
            `  <meta name="ahrefs-site-verification" content="${AHREFS}">\n</head>`
          );
        }
        if (seo.status === 404) res.status(404);

        if (!isBot(ua)) {
          setSsrToCache(url, html, res.statusCode || 200);
        }
      }
      // нормализуем ссылки на ассеты и base
      html = html
        .replace(/https:\/\/assets\//g, "/assets/")
        .replace(/([("'=\s])\/\/assets\//g, "$1/assets/");
      res.set({ "Content-Type": "text/html" }).end(html);
    } catch (e) {
      if (!isProduction && vite) {
        vite.ssrFixStacktrace(e);
      }
      console.error("SSR Error:", e);
      next(e);
    }
  });

  // Warm the big JSON cache once at startup to avoid concurrent first-loads
  await readData();

  // Запуск сервера
  app.listen(PORT, () => {
    console.log(`Сервер запущен на порту ${PORT}`);
    console.log(`API доступен по адресу: http://localhost:${PORT}/api`);
    console.log(
      `Статические файлы доступны по адресу: http://localhost:${PORT}`
    );
  });

  return app;
}

// Запускаем сервер
createServerApp().catch(console.error);
