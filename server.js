require("dotenv").config({ path: "./config.env" });
const express = require("express");
const fs = require("fs").promises;
const fsSync = require("fs");
const path = require("path");
const cors = require("cors");
const axios = require("axios");
const compression = require("compression");

async function createServerApp() {
  const app = express();
  const PORT = process.env.SERVER_PORT || 3000;
  const BASE_URL = process.env.PUBLIC_BASE_URL || `http://localhost:${PORT}`;
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
          links += `<link rel="preload" as="style" href="/${file}" onload="this.onload=null;this.rel='stylesheet'">` +
            `<noscript><link rel="stylesheet" href="/${file}"></noscript>`;
        } else if (file.endsWith(".woff2") || file.endsWith(".woff")) {
          const type = file.endsWith(".woff2") ? "font/woff2" : "font/woff";
          links += `<link rel="preload" href="/${file}" as="font" type="${type}" crossorigin>`;
        }
      }
    });
    return links;
  }
  // Middleware
  app.use(cors());
  app.use(express.json());
  app.use(compression());

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
  const DATA_FILE = path.join(__dirname, "movies-data.json");
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
  function isRecentPremiere(movie) {
    const d = parseRussianPremiere(movie?.premiere);
    return !!(d && isTodayOrYesterday(d));
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
      const t = Number(process.env.HOME_POP_DORAMAS || process.env.HOME_POP_DEFAULT || 5);
      return p >= t;
    }
    if (String(special) === "turkish") {
      const t = Number(process.env.HOME_POP_TURKISH || process.env.HOME_POP_DEFAULT || 5);
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
      (m) => m.category === name && m.id !== "index" && !isRecentPremiere(m)
    );

    const availableYears = [
      ...new Set(movies.map((m) => m.year).filter(Boolean)),
    ].sort((a, b) => b - a);
    const availableGenres = Array.from(
      movies.reduce((acc, m) => {
        (m.genres || []).forEach((g) => acc.add(g));
        return acc;
      }, new Set())
    ).sort();

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
    if (genre)
      filtered = filtered.filter((m) =>
        (m.genres || []).includes(String(genre))
      );
    if (country)
      filtered = filtered.filter((m) =>
        String(m.country || "")
          .toLowerCase()
          .includes(String(country).toLowerCase())
      );
    if (translation)
      filtered = filtered.filter((m) =>
        (m.translation || "").includes(String(translation))
      );
    if (actor)
      filtered = filtered.filter((m) =>
        String(m.actors || "").includes(String(actor))
      );

    // Ограничение для вкладки "По рейтингу" на главной: только последние N лет
    if (opts.home && sort === "rating") {
      const currentYear = new Date().getFullYear();
      const span =
        Math.max(1, parseInt(process.env.HOME_RATING_YEARS, 10) || 3);
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
    if (!movie) return null;

    const categories = data?.categories || {};
    const related = (data?.movies || [])
      .filter(
        (m) =>
          m.id !== movie.id &&
          m.category === movie.category &&
          Array.isArray(m.genres) &&
          Array.isArray(movie.genres) &&
          m.genres.some((g) => movie.genres.includes(g))
      )
      .slice(0, 6)
      .map(categoryCardFields);

    return { movie, categories, related };
  }

  function buildHomeFeed(data) {
    const all = (data?.movies || []).filter(
      (m) => m.id !== "index" && !isRecentPremiere(m)
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
    const cat = (name) => pickLatest(allowed.filter((m) => m.category === name));
    const doramas = pickLatest(
      allowedDoramas.filter(
        (m) =>
          m.category === "serialy" &&
          isAsianCountry(m.country) &&
          !isTurkish(m.country)
      )
    );
    const turkish = pickLatest(
      allowedTurkish.filter((m) => m.category === "serialy" && isTurkish(m.country))
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
      (m) => m.id !== "index" && ratingOf(m) > 0 && !isRecentPremiere(m)
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
    categoryFeedCache.set(key, { mtime: lastModifiedTime, data: feed });
    return feed;
  }

  function getTopFeedPaged(data, options) {
    const key = JSON.stringify({ ...options });
    const cached = topFeedCache.get(key);
    if (cached && cached.mtime === lastModifiedTime) {
      return cached.data;
    }
    const feed = buildTopFeedPaged(data, options);
    topFeedCache.set(key, { mtime: lastModifiedTime, data: feed });
    return feed;
  }

  // Функция для чтения данных
  async function readData() {
    try {
      const stats = await fs.stat(DATA_FILE);
      // Если файл не менялся с последнего чтения, возвращаем кэш
      if (
        moviesDataCache &&
        lastModifiedTime &&
        stats.mtimeMs === lastModifiedTime
      ) {
        return moviesDataCache;
      }

      // Иначе читаем файл заново
      console.log("File has changed, updating movie data cache...");
      const data = await fs.readFile(DATA_FILE, "utf8");
      moviesDataCache = JSON.parse(data);
      lastModifiedTime = stats.mtimeMs; // Сохраняем время последней модификации
      return moviesDataCache;
    } catch (error) {
      console.error("Ошибка чтения файла:", error);
      // При ошибке сбрасываем кэш
      moviesDataCache = null;
      lastModifiedTime = null;
      return null;
    }
  }

  // Хелперы для серверных стораджей
  async function ensureDataDir() {
    try {
      await fs.mkdir(DATA_DIR, { recursive: true });
    } catch (_) { }
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
    return html.replace(/<link\s+rel=["']stylesheet["'][^>]*href=["'](\/assets\/[^"']+\.css)["'][^>]*>\s*/gi, (m, href) => {
      const hasCross = /crossorigin/i.test(m) ? ' crossorigin' : '';
      const mediaMatch = m.match(/\smedia=["']([^"']+)["']/i);
      const mediaAttr = mediaMatch ? ` media="${mediaMatch[1]}"` : '';
      return `<link rel="preload" as="style" href="${href}"${hasCross}${mediaAttr} onload="this.onload=null;this.rel='stylesheet'">` +
             `<noscript><link rel="stylesheet" href="${href}"${hasCross}${mediaAttr}></noscript>`;
    });
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

  app.get("/api/movies-data", async (req, res) => {
    try {
      const data = await readData();
      res.json(data || { movies: [], categories: {} });
    } catch (e) {
      res.status(500).json({ movies: [], categories: {} });
    }
  });

  app.get("/api/search", async (req, res) => {
    try {
      const q = String(req.query.q || "").toLowerCase();
      if (!q) return res.json([]);
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
            !isRecentPremiere(m) &&
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
      res.json(found);
    } catch (e) {
      res.status(500).json([]);
    }
  });

  // GET /api/movie/:id — один фильм
  app.get("/api/movie/:id", async (req, res) => {
    const data = await readData();
    const m = (data?.movies || []).find((x) => x.id === req.params.id);
    if (!m) return res.status(404).json({ error: "not_found" });
    res.json({ movie: m, categories: data?.categories || {} });
  });

  // Home feed for landing page
  app.get("/api/home-feed", async (req, res) => {
    try {
      const data = await readData();
      res.json(getHomeFeed(data));
    } catch {
      res.status(500).json({ popular: [], sections: {} });
    }
  });

  app.get("/api/movie-full/:id", async (req, res) => {
    try {
      const data = await readData();
      const payload = buildMoviePayload(data, String(req.params.id));
      if (!payload) return res.status(404).json({ error: "not_found" });
      res.json(payload);
    } catch {
      res.status(500).json({ error: "server_error" });
    }
  });

  app.get("/api/category", async (req, res) => {
    try {
      const data = await readData();
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
      res.json(feed);
    } catch (e) {
      res.status(500).json({ items: [], total: 0, totalPages: 1 });
    }
  });

  // Top list
  app.get("/api/top", async (req, res) => {
    try {
      const data = await readData();
      const limit = Math.max(
        1,
        Math.min(200, parseInt(req.query.limit, 10) || 24)
      );
      const offset = Math.max(0, parseInt(req.query.offset, 10) || 0);
      const type = String(req.query.type || "all");
      const result = getTopFeedPaged(data, { limit, offset, type });
      res.json(result);
    } catch {
      res.status(500).json({ items: [], total: 0 });
    }
  });

  // Related movies for a given id (lightweight for hard-reload cases)
  app.get("/api/related/:id", async (req, res) => {
    try {
      const data = await readData();
      const id = String(req.params.id);
      const list = data?.movies || [];
      const cur = list.find((m) => m.id === id);
      if (!cur) return res.json({ items: [] });

      const items = list
        .filter(
          (m) =>
            m.id !== id &&
            m.category === cur.category &&
            Array.isArray(m.genres) &&
            Array.isArray(cur.genres) &&
            m.genres.some((g) => cur.genres.includes(g))
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

      res.json({ items });
    } catch {
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
    let list = (data?.movies || []).filter((m) => m.id !== "index");

    if (category) list = list.filter((m) => m.category === String(category));
    if (year) list = list.filter((m) => String(m.year) === String(year));
    if (genre)
      list = list.filter((m) => (m.genres || []).includes(String(genre)));
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

      const data = await readData();
      if (!data || !data.movies) {
        return res.status(500).json({ error: "Could not load movie data." });
      }

      // /api/search-suggestions
      const suggestions = data.movies
        .filter(
          (movie) =>
            movie.id !== "index" &&
            !isRecentPremiere(movie) &&
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

      res.json(suggestions);
    } catch (error) {
      console.error("Ошибка поиска:", error);
      res.status(500).json({ error: "Внутренняя ошибка сервера" });
    }
  });

  // API endpoint для голосования за страницу
  app.post("/api/vote-page", async (req, res) => {
    try {
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

  // On-the-fly ресайз постеров: /img?src=/uploads/posts/foo.jpg&w=360&q=70&f=webp
  app.get("/img", async (req, res) => {
    try {
      const src = String(req.query.src || "");
      const w = Math.max(1, Math.min(1200, parseInt(req.query.w, 10) || 360));
      const q = Math.max(1, Math.min(95, parseInt(req.query.q, 10) || 70));
      const f = String(req.query.f || "webp").toLowerCase(); // webp|jpeg|avif
      const abs = path.join(__dirname, src.replace(/^\//, ""));
      if (!fsSync.existsSync(abs)) return res.status(404).send("not found");
      const sharp = require("sharp");
      let img = sharp(abs).resize({ width: w, withoutEnlargement: true });
      if (f === "avif") img = img.avif({ quality: q });
      else if (f === "jpeg" || f === "jpg")
        img = img.jpeg({ quality: q, mozjpeg: true });
      else img = img.webp({ quality: q });
      res.setHeader("Cache-Control", "public, max-age=31536000, immutable");
      res.type(f === "jpeg" ? "jpeg" : f);
      img.pipe(res);
    } catch {
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

      console.log("[probe]", { host, status, matched, looksBad });
      const debug = String(req.query.debug || "") === "1";
      const sample = body.slice(0, 800);

      console.log("[probe-full]", {
        host,
        status,
        matched,
        looksBad,
        sample: sample.replace(/\n/g, " "),
      });

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
      const upstream = "https://stage.player.cdnvideohub.com/static/playerui.js";
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
        return res.status(502).type("application/javascript").send("// cdnvh proxy: upstream failed");
      }
      res.set("Content-Type", "application/javascript; charset=utf-8");
      res.set("Cache-Control", "public, max-age=2592000, immutable"); // 30d
      res.send(resp.data);
    } catch (e) {
      res.status(502).type("application/javascript").send("// cdnvh proxy: request failed");
    }
  });

  app.get("/api/cdnvh-umd.js", async (req, res) => {
    try {
      const upstream = "https://player.cdnvideohub.com/s2/stable/video-player.umd.js";
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
        return res.status(502).type("application/javascript").send("// cdnvh umd proxy: upstream failed");
      }
      res.set("Content-Type", "application/javascript; charset=utf-8");
      // 30 days. You can use 1y + immutable if you always bump the path when upstream changes.
      res.set("Cache-Control", "public, max-age=2592000, immutable");
      res.send(resp.data);
    } catch (e) {
      res.status(502).type("application/javascript").send("// cdnvh umd proxy: request failed");
    }
  });

  app.get("/api/ym-tag.js", async (req, res) => {
    try {
      const upstream = "https://mc.yandex.ru/metrika/tag.js";
      const resp = await axios.get(upstream, {
        timeout: 10000,
        headers: { "User-Agent": "Mozilla/5.0", Accept: "application/javascript,text/javascript,*/*;q=0.1" },
        responseType: "text",
        validateStatus: () => true,
      });
      if (resp.status >= 400 || !resp.data) {
        return res.status(502).type("application/javascript").send("// ym proxy: upstream failed");
      }
      res.set("Content-Type", "application/javascript; charset=utf-8");
      res.set("Cache-Control", "public, max-age=2592000, immutable");
      res.send(resp.data);
    } catch (e) {
      res.status(502).type("application/javascript").send("// ym proxy: request failed");
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
      res.set("Cache-Control", "public, max-age=3600");
      res.send(resp.data);
    } catch (e) {
      res
        .status(502)
        .type("application/javascript")
        .send("// kd proxy: request failed");
    }
  });

  // SEO: robots.txt
  app.get("/robots.txt", (req, res) => {
    res.type("text/plain").send(
      `User-agent: *
Allow: /
Sitemap: ${BASE_URL}/sitemap.xml
`
    );
  });

  // SEO: sitemap.xml
  app.get("/sitemap.xml", async (req, res) => {
    try {
      const data = await readData();
      const movies = (data?.movies || []).filter(
        (m) => m.id !== "index" && !isRecentPremiere(m)
      );
      const now = new Date().toISOString().split("T")[0];

      const urls = [
        { loc: `${BASE_URL}/`, priority: "1.0" },
        { loc: `${BASE_URL}/filmy`, priority: "0.8" },
        { loc: `${BASE_URL}/serialy`, priority: "0.8" },
        { loc: `${BASE_URL}/multfilmy`, priority: "0.8" },
        { loc: `${BASE_URL}/anime`, priority: "0.8" },
      ].concat(
        movies.map((m) => ({
          loc: `${BASE_URL}/${m.category}/${m.id}`,
          priority: "0.6",
        }))
      );

      const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls
          .map(
            (u) => `  <url>
    <loc>${u.loc}</loc>
    <lastmod>${now}</lastmod>
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

    const seo = {
      title: "LordFilm — фильмы, сериалы и аниме онлайн",
      description:
        "Смотрите фильмы, сериалы и аниме онлайн в HD без регистрации — LordFilm.",
      canonical: BASE_URL + "/",
      ogImage: null,
      robots: "index,follow",
      ldJson: null,
      status: 200,
      ogType: "website",
    };

    if (path === "/") return seo;

    if (path === "/tops") {
      seo.title = "Топ всех фильмов и сериалов — LordFilms";
      seo.description =
        "Рейтинг фильмов и сериалов: лучшие по версиям IMDb/Кинопоиск на LordFilms.";
      seo.canonical = `${BASE_URL}/tops`;
      return seo;
    }

    const knownCats = ["filmy", "serialy", "multfilmy", "anime"];
    const parts = path.split("/").filter(Boolean);

    // Category root: /filmy, /serialy, /multfilmy, /anime
    if (knownCats.includes(path.slice(1))) {
      const cat = path.slice(1);
      const name =
        categories[cat] ||
        {
          filmy: "Фильмы",
          serialy: "Сериалы",
          multfilmy: "Мультфильмы",
          anime: "Аниме",
        }[cat] ||
        "Контент";
      seo.title = `${name} смотреть онлайн — LordFilms`;
      seo.description = `${name} в хорошем качестве без рекламы — онлайн на LordFilms.`;
      seo.canonical = `${BASE_URL}/${cat}`;
      return seo;
    }

    // Movie: /:category/:id
    if (parts.length === 2) {
      const [cat, id] = parts;
      const m = movies.find((x) => x.id === id);
      if (!m) {
        seo.title = "Страница не найдена — LordFilms";
        seo.description = "Страница не найдена.";
        seo.canonical = `${BASE_URL}${path}`;
        seo.robots = "noindex,follow";
        seo.status = 404;
        return seo;
      }
      const year = m.year ? ` (${m.year})` : "";
      seo.title = `${m.title}${year} смотреть онлайн — LordFilms`;
      const desc =
        truncate(stripTags(m.description), 300) ||
        `${m.title}${year} смотреть онлайн в хорошем качестве.`;
      seo.description = desc;
      seo.canonical = `${BASE_URL}/${m.category}/${m.id}`;
      seo.ogImage = m.image
        ? m.image.startsWith("http")
          ? m.image
          : `${BASE_URL}/${m.image.startsWith("/") ? m.image.slice(1) : m.image}`
        : null;

      const rating = m.imdbRating || m.kpRating;
      const ld = {
        "@context": "https://schema.org",
        "@type": "Movie",
        name: m.title,
        datePublished: m.year ? String(m.year) : undefined,
        image: seo.ogImage || undefined,
        description: desc,
        aggregateRating: rating
          ? {
              "@type": "AggregateRating",
              ratingValue: Number(rating),
              bestRating: 10,
              ratingCount: 100,
            }
          : undefined,
      };
      seo.ldJson = JSON.stringify(ld);
      return seo;
    }

    // Any other URL under a known category (e.g. /serialy/.../page/4) => 404
    if (parts.length > 0 && knownCats.includes(parts[0])) {
      seo.title = "Страница не найдена — LordFilms";
      seo.description = "Страница не найдена.";
      seo.canonical = `${BASE_URL}${path}`;
      seo.robots = "noindex,follow";
      seo.status = 404;
      return seo;
    }

    // Any other unknown path => 404
    seo.title = "Страница не найдена — LordFilms";
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
    if (p === "/tops") return { type: "tops" };
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

  function injectSeo(html, seo) {
    // title
    html = html.replace(
      /<title>[\s\S]*?<\/title>/i,
      `<title>${seo.title}</title>`
    );

    // meta description (upsert)
    if (/<meta\s+name=["']description["'][^>]*>/i.test(html)) {
      html = html.replace(
        /<meta\s+name=["']description["'][^>]*>/i,
        `<meta name="description" content="${seo.description}">`
      );
    } else {
      html = html.replace(
        "</head>",
        `  <meta name="description" content="${seo.description}">\n</head>`
      );
    }

    // robots
    if (seo.robots) {
      if (/<meta\s+name=["']robots["'][^>]*>/i.test(html)) {
        html = html.replace(
          /<meta\s+name=["']robots["'][^>]*>/i,
          `<meta name="robots" content="${seo.robots}">`
        );
      } else {
        html = html.replace(
          "</head>",
          `  <meta name="robots" content="${seo.robots}">\n</head>`
        );
      }
    }

    // canonical (upsert)
    if (/<link\s+rel=["']canonical["'][^>]*>/i.test(html)) {
      html = html.replace(
        /<link\s+rel=["']canonical["'][^>]*>/i,
        `<link rel="canonical" href="${seo.canonical}">`
      );
    } else {
      html = html.replace(
        "</head>",
        `  <link rel="canonical" href="${seo.canonical}">\n</head>`
      );
    }

    // OpenGraph
    const og = [
      ["og:type", seo.ogType || "website"],
      ["og:title", seo.title],
      ["og:description", seo.description],
      ["og:url", seo.canonical],
    ];
    if (seo.ogImage) og.push(["og:image", seo.ogImage]);
    for (const [prop, content] of og) {
      const re = new RegExp(`<meta\\s+property=["']${prop}["'][^>]*>`, "i");
      const tag = `<meta property="${prop}" content="${content}">`;
      html = re.test(html)
        ? html.replace(re, tag)
        : html.replace("</head>", `  ${tag}\n</head>`);
    }

    // Twitter
    const tw = [
      ["twitter:card", seo.ogImage ? "summary_large_image" : "summary"],
      ["twitter:title", seo.title],
      ["twitter:description", seo.description],
    ];
    if (seo.ogImage) tw.push(["twitter:image", seo.ogImage]);
    for (const [name, content] of tw) {
      const re = new RegExp(`<meta\\s+name=["']${name}["'][^>]*>`, "i");
      const tag = `<meta name="${name}" content="${content}">`;
      html = re.test(html)
        ? html.replace(re, tag)
        : html.replace("</head>", `  ${tag}\n</head>`);
    }

    // JSON-LD
    if (seo.ldJson) {
      const tag = `<script type="application/ld+json">${seo.ldJson}</script>`;
      html = html.replace("</head>", `  ${tag}\n</head>`);
    }

    return html;
  }

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
        const data = await readData();

        // Сборка initialState по типу маршрута
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
        html = injectSeo(html, seo);
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
        const stateScript = scripts.length
          ? `<script>${scripts.join(";")}</script>`
          : "";

          let htmlBase = injectPreloadLinks(template, preload)
          .replace("<!--ssr-outlet-->", appHtml)
          .replace("<!--initial-state-->", stateScript);
        
        try {
          const { default: Critters } = await import('critters');
          const critters = new Critters({
            path: path.resolve('dist/client'),
            publicPath: '/',
            preload: 'swap',       // неблокирующая загрузка остатка CSS
            pruneSource: false,    // не вырезаем исходный CSS-файл
            reduceInlineStyles: false
          });
          html = await critters.process(htmlBase);
        } catch (_) {
          // Фолбэк: оставляем ваш неблокирующий конвертер
          const withNonBlockingCss = transformStylesheetsToPreload(htmlBase);
          html = withNonBlockingCss;
        }

        const seo = computeSeo(url, data, BASE_URL);
        html = injectSeo(html, seo);
        if (seo.status === 404) res.status(404);
      }

      res.set({ "Content-Type": "text/html" }).end(html);
    } catch (e) {
      if (!isProduction && vite) {
        vite.ssrFixStacktrace(e);
      }
      console.error("SSR Error:", e);
      next(e);
    }
  });

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
