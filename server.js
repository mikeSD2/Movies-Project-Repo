require('dotenv').config({ path: './config.env' })
const express = require('express')
const fs = require('fs').promises
const fsSync = require('fs')
const path = require('path')
const cors = require('cors')

const app = express()
const PORT = process.env.SERVER_PORT || 3001

// Middleware
app.use(cors())
app.use(express.json())
app.use(express.static('.')) // Serve static files

// Путь к файлу с данными
const DATA_FILE = path.join(__dirname, 'movies-data.json')
// Серверные (только backend) хранилища, чтобы не триггерить HMR фронтенда
const DATA_DIR = path.join(__dirname, 'server-data')
const COMMENTS_FILE = path.join(DATA_DIR, 'comments-store.json')
const RATINGS_FILE = path.join(DATA_DIR, 'ratings-store.json')

let moviesDataCache = null

// Функция для чтения данных
async function readData() {
  if (moviesDataCache) {
    return moviesDataCache
  }
  try {
    const data = await fs.readFile(DATA_FILE, 'utf8')
    moviesDataCache = JSON.parse(data)
    return moviesDataCache
  } catch (error) {
    console.error('Ошибка чтения файла:', error)
    return null
  }
}

// Хелперы для серверных стораджей
async function ensureDataDir() {
  try {
    await fs.mkdir(DATA_DIR, { recursive: true })
  } catch (_) {}
}

async function readStore(filePath, fallbackValue) {
  await ensureDataDir()
  try {
    const raw = await fs.readFile(filePath, 'utf8')
    return JSON.parse(raw)
  } catch (error) {
    return fallbackValue
  }
}

async function writeStore(filePath, data) {
  await ensureDataDir()
  await fs.writeFile(filePath, JSON.stringify(data, null, 2), 'utf8')
}

// Комментарии: хранение по ключу movieId -> Comment[]
async function getCommentsStore() {
  return readStore(COMMENTS_FILE, {})
}

async function setCommentsStore(store) {
  await writeStore(COMMENTS_FILE, store)
}

async function getCommentsForMovie(movieId) {
  const store = await getCommentsStore()
  if (!store[movieId]) {
    // Ленивая инициализация из movies-data.json (если есть)
    const data = await readData()
    const movie = data?.movies.find(m => m.id === movieId)
    store[movieId] = movie?.comments || []
    await setCommentsStore(store)
  }
  return store[movieId]
}

async function saveCommentsForMovie(movieId, comments) {
  const store = await getCommentsStore()
  store[movieId] = comments
  await setCommentsStore(store)
  return comments
}

// Рейтинги страниц: хранение по ключу movieId -> { pageLikes, pageDislikes }
async function getRatingsStore() {
  return readStore(RATINGS_FILE, {})
}

async function setRatingsStore(store) {
  await writeStore(RATINGS_FILE, store)
}

async function getRatingsForMovie(movieId) {
  const store = await getRatingsStore()
  if (!store[movieId]) {
    // Ленивая инициализация из movies-data.json (если есть)
    const data = await readData()
    const movie = data?.movies.find(m => m.id === movieId)
    store[movieId] = {
      pageLikes: movie?.pageLikes || 0,
      pageDislikes: movie?.pageDislikes || 0
    }
    await setRatingsStore(store)
  }
  return store[movieId]
}

async function saveRatingsForMovie(movieId, ratings) {
  const store = await getRatingsStore()
  store[movieId] = ratings
  await setRatingsStore(store)
  return ratings
}

app.get('/api/search-suggestions', async (req, res) => {
  try {
    const { q } = req.query
    if (!q || q.length < 1) {
      return res.json([])
    }

    const data = await readData()
    if (!data || !data.movies) {
      return res.status(500).json({ error: 'Could not load movie data.' })
    }

    const suggestions = data.movies
      .filter(movie => 
        movie.title.toLowerCase().includes(q.toLowerCase()) ||
        (movie.originalTitle && movie.originalTitle.toLowerCase().includes(q.toLowerCase()))
      )
      .slice(0, 5)
      .map(movie => ({
        id: movie.id,
        title: movie.title,
        category: movie.category,
        year: movie.year,
        poster: movie.image, // Используем поле 'image' для постеров
        genres: movie.genres ? movie.genres.slice(0, 3) : [],
        kpRating: movie.kpRating,
        imdbRating: movie.imdbRating
      }))

    res.json(suggestions)
  } catch (error) {
    console.error('Ошибка поиска:', error)
    res.status(500).json({ error: 'Внутренняя ошибка сервера' })
  }
})

// API endpoint для голосования за страницу
app.post('/api/vote-page', async (req, res) => {
  try {
    const { movieId, voteType, previousVote } = req.body
    
    if (!movieId) {
      return res.status(400).json({ error: 'Неверные параметры: отсутствует movieId' })
    }
    
    // voteType может быть null когда пользователь отменяет голос
    if (voteType !== 'like' && voteType !== 'dislike' && voteType !== null) {
      return res.status(400).json({ error: 'Неверные параметры: voteType должен быть like, dislike или null' })
    }
    
    // Читаем/инициализируем серверное хранилище рейтингов
    const ratings = await getRatingsForMovie(movieId)
    
    // Обновляем оценки
    if (previousVote === 'like') ratings.pageLikes--
    if (previousVote === 'dislike') ratings.pageDislikes--
    
    if (voteType === 'like') ratings.pageLikes++
    if (voteType === 'dislike') ratings.pageDislikes++
    
    await saveRatingsForMovie(movieId, ratings)
    
    res.json({
      success: true,
      pageLikes: ratings.pageLikes,
      pageDislikes: ratings.pageDislikes
    })
    
  } catch (error) {
    console.error('Ошибка голосования:', error)
    res.status(500).json({ error: 'Внутренняя ошибка сервера' })
  }
})

// API endpoint для получения оценок фильма
app.get('/api/movie-ratings/:movieId', async (req, res) => {
  try {
    const { movieId } = req.params
    const ratings = await getRatingsForMovie(movieId)
    res.json({
      pageLikes: ratings.pageLikes || 0,
      pageDislikes: ratings.pageDislikes || 0
    })
  } catch (error) {
    console.error('Ошибка получения оценок:', error)
    res.status(500).json({ error: 'Внутренняя ошибка сервера' })
  }
})

// API endpoint для получения всех оценок
app.get('/api/all-ratings', async (req, res) => {
  try {
    const ratings = await getRatingsStore()
    res.json(ratings)
  } catch (error) {
    console.error('Ошибка получения всех оценок:', error)
    res.status(500).json({ error: 'Внутренняя ошибка сервера' })
  }
})

// API endpoint для добавления комментария
app.post('/api/add-comment', async (req, res) => {
  try {
    const { name, comment, movieId, parentId, 'g-recaptcha-response': recaptchaToken } = req.body
    
    if (!name || !comment || !movieId) {
      return res.status(400).json({ error: 'Неверные параметры' })
    }
    
    // Проверяем reCAPTCHA с secret key из .env
    if (!recaptchaToken) {
      return res.status(400).json({ error: 'Необходимо подтвердить reCAPTCHA' })
    }
    
    // В реальном приложении здесь была бы проверка токена с Google
    // const recaptchaVerification = await verifyRecaptcha(recaptchaToken, process.env.RECAPTCHA_SECRET_KEY)
    
    // Создаем новый комментарий
    const newComment = {
      id: Date.now(),
      name: name || 'Гость',
      comment,
      date: new Date().toLocaleDateString('ru-RU'),
      rating: 0,
      userVote: null,
      parentId: parentId || null
    }
    
    const comments = await getCommentsForMovie(movieId)
    comments.push(newComment)
    await saveCommentsForMovie(movieId, comments)
    
    res.json({
      success: true,
      comment: newComment,
      commentsCount: comments.length
    })
    
  } catch (error) {
    console.error('Ошибка добавления комментария:', error)
    res.status(500).json({ error: 'Внутренняя ошибка сервера' })
  }
})

// API endpoint для получения комментариев фильма
app.get('/api/movie-comments/:movieId', async (req, res) => {
  try {
    const { movieId } = req.params
    const comments = await getCommentsForMovie(movieId)
    res.json({
      comments,
      commentsCount: comments.length
    })
  } catch (error) {
    console.error('Ошибка получения комментариев:', error)
    res.status(500).json({ error: 'Внутренняя ошибка сервера' })
  }
})

// API endpoint для голосования за комментарий
app.post('/api/vote-comment', async (req, res) => {
  try {
    const { movieId, commentId, voteType, previousVote } = req.body
    
    if (!movieId || !commentId) {
      return res.status(400).json({ error: 'Неверные параметры' })
    }
    
    // voteType может быть null когда пользователь отменяет голос
    if (voteType !== 'like' && voteType !== 'dislike' && voteType !== null) {
      return res.status(400).json({ error: 'Неверные параметры: voteType должен быть like, dislike или null' })
    }
    
    const comments = await getCommentsForMovie(movieId)
    const comment = comments.find(c => c.id === commentId)
    if (!comment) {
      return res.status(404).json({ error: 'Комментарий не найден' })
    }
    
    if (typeof comment.rating === 'undefined') comment.rating = 0
    if (typeof comment.userVote === 'undefined') comment.userVote = null
    
    // Обновляем рейтинг комментария
    if (previousVote === 'like') comment.rating--
    if (previousVote === 'dislike') comment.rating++
    
    if (voteType === 'like') comment.rating++
    if (voteType === 'dislike') comment.rating--
    
    // Обновляем userVote
    comment.userVote = voteType
    
    await saveCommentsForMovie(movieId, comments)
    
    res.json({
      success: true,
      comment: comment
    })
    
  } catch (error) {
    console.error('Ошибка голосования за комментарий:', error)
    res.status(500).json({ error: 'Внутренняя ошибка сервера' })
  }
})

// Запуск сервера
app.listen(PORT, () => {
  console.log(`Сервер запущен на порту ${PORT}`)
  console.log(`API доступен по адресу: http://localhost:${PORT}/api`)
  console.log(`Статические файлы доступны по адресу: http://localhost:${PORT}`)
})
