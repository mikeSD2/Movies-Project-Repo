require("dotenv").config({ path: "./config.env" });
const express = require("express");
const fs = require("fs").promises;
const fsSync = require("fs");
const path = require("path");
const cors = require("cors");
const axios = require("axios");

const app = express();
const PORT = process.env.SERVER_PORT || 3002;
const BASE_URL = process.env.PUBLIC_BASE_URL || `http://localhost:${PORT}`;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(".")); // Serve static files

// Путь к файлу с данными
const DATA_FILE = path.join(__dirname, "movies-data.json");
// Серверные (только backend) хранилища, чтобы не триггерить HMR фронтенда
const DATA_DIR = path.join(__dirname, "server-data");
const COMMENTS_FILE = path.join(DATA_DIR, "comments-store.json");
const RATINGS_FILE = path.join(DATA_DIR, "ratings-store.json");

let moviesDataCache = null;
let lastModifiedTime = null;

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
          movie.title.toLowerCase().includes(q.toLowerCase()) ||
          (movie.originalTitle &&
            movie.originalTitle.toLowerCase().includes(q.toLowerCase()))
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
      return res
        .status(400)
        .json({
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
      return res
        .status(400)
        .json({
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

// Probe external player URL (server-side) to detect "content not found" pages
app.get('/api/probe-player', async (req, res) => {
  try {
    const { url } = req.query;
    if (!url) return res.status(400).json({ ok: false, error: 'Missing url' });

    const u = new URL(url);
    const host = u.hostname;

    const resp = await axios.get(url, {
      timeout: 8000,
      headers: {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': BASE_URL,
      },
      validateStatus: () => true,
    });

    const status = resp.status || 0;
    const body = typeof resp.data === 'string' ? resp.data : '';

    // Фразы ошибки, которые реально показывает Alloha
    const matchedSpecific =
      /К сожалению,\s*(?:запрашиваемый контент не найден|видео недоступно)/i.test(body) ||
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
      looksBad = status >= 400 || matchedSpecific || matchedTitle || matched404;
    }

    console.log('[probe]', { host, status, matched, looksBad });
    const debug = String(req.query.debug || '') === '1';
    const sample = body.slice(0, 800);

    console.log('[probe-full]', { host, status, matched, looksBad, sample: sample.replace(/\n/g,' ') });

    if (debug) {
      return res.json({ ok: !looksBad, status, matched, host, looksBad, sample });
    }
    res.json({ ok: !looksBad, status, matched, host });
  } catch (e) {
    const debug = String(req.query.debug || '') === '1';

    // Попробуем вытащить данные из axios-ошибки (если они есть)
    const host = (() => {
      try { return new URL(String(req.query.url || '')).hostname } catch { return null }
    })();
    const status = e?.response?.status || 0;
    const body = typeof e?.response?.data === 'string' ? e.response.data : '';
    const sample = body.slice(0, 800);

    console.error('[probe-error]', { host, status, message: e?.message });
    if (debug) {
      return res.json({
        ok: false,
        host,
        status,
        matched: false,
        looksBad: true,
        sample,
        error: e?.message || 'request-failed'
      });
    }
    return res.json({ ok: false, error: 'request-failed' });
  }
});


// Прокси для загрузчика Kodik, чтобы обойти блокировки/AdBlock
app.get('/api/kd-loader.js', async (req, res) => {
  try {
    const upstream = 'https://kodik-add.com/add-players.min.js'
    const resp = await axios.get(upstream, {
      timeout: 10000,
      headers: {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/javascript,text/javascript,*/*;q=0.1',
        'Referer': BASE_URL,
      },
      responseType: 'text',
      validateStatus: () => true,
    })
    if (resp.status >= 400 || !resp.data) {
      return res.status(502).type('application/javascript').send('// kd proxy: upstream failed')
    }
    res.set('Content-Type', 'application/javascript; charset=utf-8')
    res.set('Cache-Control', 'public, max-age=3600')
    res.send(resp.data)
  } catch (e) {
    res.status(502).type('application/javascript').send('// kd proxy: request failed')
  }
})

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
    const movies = data?.movies || [];
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

// Запуск сервера
app.listen(PORT, () => {
  console.log(`Сервер запущен на порту ${PORT}`);
  console.log(`API доступен по адресу: http://localhost:${PORT}/api`);
  console.log(`Статические файлы доступны по адресу: http://localhost:${PORT}`);
});