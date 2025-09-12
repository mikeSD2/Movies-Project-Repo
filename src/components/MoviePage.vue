<template>
  <div v-if="isLightOff" class="light-off-overlay" @click="isLightOff = false"></div>
  <div v-if="movie" class="speedbar ws-nowrap">
    <router-link to="/">LordFilms</router-link> » 
    <router-link :to="`/${movie.category}`">{{ categoryTitle }}</router-link> » 
    {{ movie.title }}
  </div>
  
  <div class="grid-items count-items">
    <article v-if="movie" class="page ignore-select">
      <div class="content-page__bg">
        <div class="content-page__cols">
          <div class="content-page__cols-left">
            <div class="content-page__main">
              <div class="content-page__header">
                <h1>{{ movie.title }} 
                  <small v-if="movie.season">({{ movie.season }} | {{ movie.year }}) смотреть онлайн</small>
                  <small v-else>({{ movie.year }}) смотреть онлайн</small>
                </h1>
              </div>
              
              <div class="content-page__poster">
                <div class="content-page__img img-block ratio-2-3 img-mask">
                  <img :alt="movie.title" loading="lazy" :src="imageUrl">
                  <div v-if="movie.season" class="media__label">{{ movie.season }}</div>
                </div>
                <div class="content-page__rating-ext d-flex ai-center jc-space-between">
                  <div class="content-page__ratingscore-ring pi-center p-relative bdrs-50 ratio-1-1" style="--p:100%;">
                    {{ calculatedRating }}
                  </div>
                  <a class="page-rate-btn" :class="{ 'voted': userVote === 'like' }" data-vote-type="like" href="#" @click.prevent="votePage('like')">
                    <span class="fal fa-thumbs-up"></span>
                    <span class="page-likes-count">{{ pageLikes }}</span>
                  </a>
                  <a class="page-rate-btn" :class="{ 'voted': userVote === 'dislike' }" data-vote-type="dislike" href="#" @click.prevent="votePage('dislike')">
                    <span class="page-dislikes-count">{{ pageDislikes }}</span>
                    <span class="fal fa-thumbs-down"></span>
                  </a>
                </div>
              </div>
              
              <div class="content-page__info">
                <div class="content-page__text p-relative clearfix js-hide-text">
                  <div class="rich-text p-relative movie-descr" v-html="movie.description"></div>
                </div>
                
                <ul class="content-page__list">
                  <li v-if="movie.originalTitle">
                    <span>Название:</span>
                    <span>{{ movie.originalTitle }}</span>
                  </li>
                  <li><span>Год выхода:</span><router-link :to="`/${movie.category}?year=${movie.year}`">{{ movie.year }}</router-link></li>
                  <li v-if="movie.country">
                    <span>Страна:</span><router-link :to="`/${movie.category}?country=${encodeURIComponent(movie.country)}`">{{ movie.country }}</router-link>
                  </li>
                  <li v-if="movie.premiere">
                    <span>Премьера:</span>{{ movie.premiere }}
                  </li>
                  <li v-if="movie.director">
                    <span>Режиссер:</span>{{ movie.director }}
                  </li>
                  <li v-if="movie.genres && movie.genres.length">
                    <span>Жанр:</span>
                    <template v-for="(genre, index) in movie.genres" :key="genre">
                      <router-link :to="`/${movie.category}?genre=${encodeURIComponent(genre)}`">{{ genre }}</router-link><span v-if="index < movie.genres.length - 1">, </span>
                    </template>
                  </li>
                  <li v-if="movie.translation">
                    <span>Перевод:</span><router-link :to="`/${movie.category}?translation=${encodeURIComponent(movie.translation)}`">{{ movie.translation }}</router-link>
                  </li>
                  <li v-if="movie.ageRating">
                    <span>Возраст:</span>{{ movie.ageRating }}
                  </li>
                  <li v-if="movie.kpRating || movie.imdbRating" class="content-page__list-rates d-flex ai-center c-gap-20">
                    <div v-if="movie.kpRating" class="content-page__list-rates-item kp">{{ movie.kpRating }}</div>
                    <div v-if="movie.imdbRating" class="content-page__list-rates-item imdb">{{ movie.imdbRating }}</div>
                  </li>
                  <li v-if="movie.actors" class="content-page__list-wide">
                    <span>В ролях:</span>{{ movie.actors }}
                  </li>
                </ul>
                
                <div class="stext-style" style="border-left: 4px solid #a0aec0; margin-top:20px; padding: 16px; border-radius: 4px; line-height: 1.7;">
                  {{ seoDescription }}
                </div>
              </div>
            </div>
            
            <h2 class="content-page__subtitle">«{{ movie.title }}» смотреть онлайн бесплатно в HD качестве</h2>
          </div>
        </div>
        
        <!-- Плеер -->
        <div class="content-page__cols">
          <div 
            class="content-page__cols-left content-page__player tabs-block nl" 
            id="player-container"
            :class="{ 'player-overlay': isLightOff }"
          >
            <div class="content-page__player-controls d-flex ai-center p-relative">
              <div class="tabs-block__select d-flex flex-1">
                <button 
                  v-for="(player, index) in players" 
                  :key="index"
                  :class="{ 'active': activeTab === index }"
                  @click="activeTab = index"
                >
                  {{ player.name }}
                </button>
              </div>
              <div class="content-page__complaint d-flex ai-center jc-space-between c-gap-20">
                <label class="content-page__light-button has-checkbox" for="light">
                  <input id="light" name="light" type="checkbox" v-model="isLightOff">
                  <span>Свет</span>
                </label>
              </div>
            </div>
            
            <div class="tabs-block__content video-inside">
              <div v-for="(player, index) in players" :key="index" v-show="activeTab === index">
                <div v-if="player.type === 'sv'" :id="`player_video_${index}`" class="sv-container">
                  <video-player
                    :id="`cdnvideohubvideoplayer_${index}`"
                    data-publisher-id="79"
                    :data-title-id="String(player.kinopoiskId)"
                    data-aggregator="kp"
                    is-show-banner="false"
                  />
                </div>
                <div v-else-if="player.type === 'iframe'" class="video-responsive video-inside adaptive-player">
                  <iframe :src="player.src" frameborder="0" scrolling="no" allowfullscreen width="800" height="452" referrerpolicy="no-referrer-when-downgrade"></iframe>
                </div>
                <div v-else-if="player.type === 'kodik'" id="kodik-player" class="video-responsive video-inside has-12345 adaptive-player"></div>
                <div v-else-if="player.type === 'youtube'" class="video-responsive video-inside has-12345">
                  <iframe allowfullscreen frameborder="0" loading="lazy" :src="player.src"></iframe>
                </div>
              </div>
            </div>
            
            <div class="content-page__player-bottom d-flex ai-center jc-space-between r-gap-20 c-gap-20">
              <div class="content-page__fav p-relative ml-auto">
                
              </div>
              <div class="content-page__likes d-flex fa-inside-1.3x">
                <a class="page-rate-btn" :class="{ 'voted': userVote === 'like' }" data-vote-type="like" href="#" @click.prevent="votePage('like')">
                  <span class="fal fa-thumbs-up"></span>
                  <span class="page-likes-count">{{ pageLikes }}</span>
                </a>
                <a class="page-rate-btn" :class="{ 'voted': userVote === 'dislike' }" data-vote-type="dislike" href="#" @click.prevent="votePage('dislike')">
                  <span class="page-dislikes-count">{{ pageDislikes }}</span>
                  <span class="fal fa-thumbs-down"></span>
                </a>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Комментарии -->
        <div class="content-page__cols">
          <div class="content-page__cols-left">
            <div class="content-page__comments">
              <div class="section__title">Комментарии ({{ commentsCount }})</div>
              <div class="content-page__comments-info fal fa-exclamation-circle">Минимальная длина комментария - 50 знаков. Комментарии модерируются</div>
              
              <!-- Main Comment Form Container -->
              <div v-if="!replyToCommentId" class="content-page__ac" id="main-comment-form">
                <form id="dle-comments-form" @submit.prevent="submitComment">
                  <div class="comment-form serv form ignore-select comment-toggle">
                    <div class="comment-form__header d-flex ai-center">
                      <input class="comment-form__input flex-grow-1" id="name" maxlength="35" name="name" placeholder="Ваше имя" type="text" v-model="commentForm.name" required/>
                      <input class="comment-form__input flex-grow-1" id="mail" maxlength="35" name="mail" placeholder="Ваш e-mail (необязательно)" type="text" v-model="commentForm.email"/>
                    </div>
                    <div class="comment-form__editor p-relative">
                      <div class="bb-editor">
                        <textarea cols="70" id="comments" name="comments" rows="10" placeholder="Ваш комментарий..." v-model="commentForm.comment" @focus="showCaptchaOnFocus" required></textarea>
                      </div>
                    </div>
                    <div class="message-info form" :class="{ 'd-none': !showCaptcha }">
                      <div class="form__row form__row--protect">
                        <label class="form__label form__label--important" for="">Защита от спама</label>
                        <div class="g-recaptcha" data-language="ru" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" data-theme="light"></div>
                      </div>
                    </div>
                    <button class="comment-form__btn" name="submit" type="submit" :disabled="!commentForm.comment || commentForm.comment.length < 50">Отправить</button>
                  </div>
                  <input name="subaction" type="hidden" value="addcomment"/>
                  <input id="post_id" name="post_id" type="hidden" :value="movie?.id"/>
                </form>
              </div>

              <div v-if="comments.length === 0" class="message-info">Комментариев еще нет. Вы можете стать первым!</div>
              <div class="content-page__comments-list" id="content-page__comments-list">
                <div id="dle-ajax-comments">
                  <div 
                    v-for="comment in processedComments" 
                    :key="comment.id" 
                    class="comment-item"
                    :style="{ 'margin-left': comment.level * 30 + 'px' }"
                  >
                    <div class="comment js-comm" :class="{ 'pos': comment.rating > 0, 'neg': comment.rating < 0 }">
                      <div class="comment__header d-flex ai-center jc-space-between">
                        <div class="comment__author">{{ comment.name }}</div>
                        <div class="comment__date">{{ comment.date }}</div>
                      </div>
                      <div class="comment__text">{{ comment.comment }}</div>
                      <div class="comment__tools">
                        <div class="comment__rating" :data-comment-id="comment.id">
                          <span class="ratingtypeplusminus">{{ comment.rating > 0 ? '+' + comment.rating : comment.rating }}</span>
                          <a class="comment__rating-btn thelike" href="#" @click.prevent="voteComment(comment.id, 'like')" :class="{ 'voted': getUserVote(comment.id) === 'like' }">
                            <span class="fal fa-thumbs-up"></span>
                          </a>
                          <a class="comment__rating-btn thedislike" href="#" @click.prevent="voteComment(comment.id, 'dislike')" :class="{ 'voted': getUserVote(comment.id) === 'dislike' }">
                            <span class="fal fa-thumbs-down"></span>
                          </a>
                        </div>
                        <a href="#" class="reply-btn" @click.prevent="replyTo(comment.id)">Ответить</a>
                      </div>
                    </div>

                    <!-- Reply Form Container -->
                    <div v-if="replyToCommentId === comment.id" class="reply-form-container">
                       <form id="dle-comments-form-reply" @submit.prevent="submitComment">
                          <div class="comment-form serv form ignore-select comment-toggle">
                            <div class="comment-form__header d-flex ai-center">
                              <input class="comment-form__input flex-grow-1" maxlength="35" name="name" placeholder="Ваше имя" type="text" v-model="commentForm.name" required/>
                              <input class="comment-form__input flex-grow-1" maxlength="35" name="mail" placeholder="Ваш e-mail (необязательно)" type="text" v-model="commentForm.email"/>
                            </div>
                            <div class="comment-form__editor p-relative">
                              <div class="bb-editor">
                                <textarea cols="70" name="comments" rows="10" placeholder="Ваш комментарий..." v-model="commentForm.comment" @focus="showCaptchaOnFocus" required></textarea>
                              </div>
                            </div>
                            <div class="message-info form" :class="{ 'd-none': !showCaptcha }">
                              <div class="form__row form__row--protect">
                                <label class="form__label form__label--important" for="">Защита от спама</label>
                                <div class="g-recaptcha" data-language="ru" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" data-theme="light"></div>
                              </div>
                            </div>
                            <div class="comment-form__actions">
                                <button class="comment-form__btn" name="submit" type="submit" :disabled="!commentForm.comment || commentForm.comment.length < 50">Отправить</button>
                                <button class="comment-form__btn cancel-btn" type="button" @click.prevent="cancelReply">Отмена</button>
                            </div>
                          </div>
                        </form>
                    </div>

                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Похожие фильмы -->
        <div v-if="relatedMovies.length" class="content-page__related carou">
          <div class="carou__caption">Смотрите также:</div>
          <div class="content-page__content carousel-grid">
            <MovieCard 
              v-for="relatedMovie in relatedMovies" 
              :key="relatedMovie.id" 
              :movie="relatedMovie" 
            />
          </div>
        </div>
      </div>
    </article>
    
    <div v-else class="no-movie">
      <h1>Фильм не найден</h1>
      <p>Возможно, фильм был удален или перемещен.</p>
      <router-link to="/" class="btn">Вернуться на главную</router-link>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import MovieCard from './MovieCard.vue'
import moviesData from '../../movies-data.json'

const route = useRoute()

const props = defineProps({
  category: String,
  id: String
})

// Найти фильм по ID
const movie = computed(() => {
  if (props.id === 'index') return undefined
  return moviesData.movies.find(m => m.id === props.id)
})

// Название категории
const categoryTitle = computed(() => {
  if (!movie.value) return ''
  return moviesData.categories[movie.value.category] || 'Контент'
})

// Функция для правильного формирования пути к изображению
const imageUrl = computed(() => {
  const img = movie.value?.image || ''
  if (!img) return ''
  if (img.startsWith('http')) return img
  return img.startsWith('/') ? img : `/${img}`
})

const players = computed(() => {
  if (!movie.value || !movie.value.kinopoiskId) return [];
  
  const playerList = [
    {
      name: 'Плеер 1',
      type: 'sv',
      kinopoiskId: movie.value.kinopoiskId,
    },
    {
      name: 'Плеер 2',
      type: 'iframe',
      src: `https://polygamist-as.stloadi.live/?kp=${movie.value.kinopoiskId}&token=eb79c8a500d725f071c3bcc1e975bb`
    },
    {
      name: 'Плеер 3',
      type: 'kodik',
      kinopoiskId: movie.value.kinopoiskId
    }
  ];

  if (movie.value.youtubeId) {
    playerList.push({
      name: 'Трейлер',
      type: 'youtube',
      src: `https://www.youtube.com/embed/${movie.value.youtubeId}`
    });
  }

  return playerList;
});

const activeTab = ref(0);
const isLightOff = ref(false);

watch(activeTab, (newIndex) => {
  const player = players.value[newIndex];
  if (!player) return;

  nextTick(() => {
    if (player.type === 'sv') {
      const containerId = `vkg_${newIndex}`;
      const container = document.getElementById(containerId);
      if (container && container.innerHTML === '') {
        // Clear previous script if any
        const oldScript = container.querySelector('script');
        if (oldScript) {
          container.removeChild(oldScript);
        }
        const script = document.createElement('script');
        script.src = 'https://stage.player.cdnvideohub.com/static/playerui.js';
        container.appendChild(script);
      }
    } else if (player.type === 'kodik') {
      const container = document.getElementById('kodik-player');
      if (container) {
        // Clear previous content
        container.innerHTML = '';

        // Remove any old loader
        const oldLoader = document.querySelector('script[src*="//kodik-add.com/add-players.min.js"]');
        if (oldLoader && oldLoader.parentNode) oldLoader.parentNode.removeChild(oldLoader);

        // Set global config as required by Kodik
        window.kodikAddPlayers = { kinopoiskID: String(player.kinopoiskId) };

        // Load official Kodik loader into head (as per docs)
        const loader = document.createElement('script');
        loader.src = '//kodik-add.com/add-players.min.js';
        loader.async = true;
        document.head.appendChild(loader);
      }
    }
  });
}, { immediate: true, deep: true });

watch(isLightOff, (newValue) => {
  const playerContainer = document.getElementById('player-container');
  if (newValue) {
    document.body.classList.add('light-off');
    if (playerContainer) {
        playerContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  } else {
    document.body.classList.remove('light-off');
  }
});


// Похожие фильмы (той же категории и жанра)
const relatedMovies = computed(() => {
  if (!movie.value) return []
  
  return moviesData.movies
    .filter(m => 
      m.id !== movie.value.id && 
      m.category === movie.value.category &&
      m.genres && movie.value.genres &&
      m.genres.some(genre => movie.value.genres.includes(genre))
    )
    .slice(0, 6)
})

// Состояние для оценок страницы
const pageLikes = ref(0)
const pageDislikes = ref(0)
const userVote = ref(null)

const calculatedRating = computed(() => {
  const likes = pageLikes.value
  const dislikes = pageDislikes.value
  const totalVotes = likes + dislikes

  if (totalVotes === 0) {
    return '0'
  }

  const rating = (likes / totalVotes) * 10
  return Math.round(rating)
})

// Состояние для комментариев
const comments = ref([])
const commentsCount = ref(0)
const replyToCommentId = ref(null) // ID комментария, на который отвечаем
const commentForm = ref({
  name: '',
  email: '',
  comment: ''
})
const showCaptcha = ref(false)

// Обработка комментариев для вложенности
const processedComments = computed(() => {
  const commentMap = {}
  comments.value.forEach(comment => {
    commentMap[comment.id] = { ...comment, children: [] }
  })

  const result = []
  comments.value.forEach(comment => {
    if (comment.parentId && commentMap[comment.parentId]) {
      commentMap[comment.parentId].children.push(commentMap[comment.id])
    } else {
      result.push(commentMap[comment.id])
    }
  })

  const flatten = (comments, level = 0) => {
    let flatList = []
    comments.forEach(comment => {
      flatList.push({ ...comment, level })
      if (comment.children.length) {
        flatList = flatList.concat(flatten(comment.children, level + 1))
      }
    })
    return flatList
  }

  return flatten(result)
})

// Загрузка оценок страницы (сервер → fallback localStorage)
const loadPageRatings = async () => {
  try {
    const resp = await fetch(`http://localhost:3001/api/movie-ratings/${props.id}`)
    if (resp.ok) {
      const { pageLikes: likes = 0, pageDislikes: dislikes = 0 } = await resp.json()
      pageLikes.value = likes
      pageDislikes.value = dislikes
    } else {
      const savedRatings = localStorage.getItem(`page_ratings_${props.id}`)
      if (savedRatings) {
        const ratings = JSON.parse(savedRatings)
        pageLikes.value = ratings.likes
        pageDislikes.value = ratings.dislikes
      } else {
        const { likes, dislikes } = calculateInitialRatings(movie.value)
        pageLikes.value = likes
        pageDislikes.value = dislikes
        localStorage.setItem(`page_ratings_${props.id}`, JSON.stringify({ likes, dislikes }))
      }
    }

    const savedVote = localStorage.getItem(`page_vote_${props.id}`)
    if (savedVote) userVote.value = savedVote
  } catch (error) {
    console.error('Ошибка загрузки оценок:', error)
    const savedRatings = localStorage.getItem(`page_ratings_${props.id}`)
    if (savedRatings) {
      const ratings = JSON.parse(savedRatings)
      pageLikes.value = ratings.likes
      pageDislikes.value = ratings.dislikes
    } else {
      const { likes, dislikes } = calculateInitialRatings(movie.value)
      pageLikes.value = likes
      pageDislikes.value = dislikes
      localStorage.setItem(`page_ratings_${props.id}`, JSON.stringify({ likes, dislikes }))
    }
    const savedVote = localStorage.getItem(`page_vote_${props.id}`)
    if (savedVote) userVote.value = savedVote
  }
}

// Функция для расчета начальных оценок на основе рейтинга фильма
const calculateInitialRatings = (movie) => {
  let rating = 0
  
  // Используем KP рейтинг если есть, иначе IMDB
  if (movie.kpRating) {
    rating = parseFloat(movie.kpRating)
  } else if (movie.imdbRating) {
    rating = parseFloat(movie.imdbRating)
  } else {
    // Если рейтинга нет, используем средние значения
    rating = 7.0
  }
  
  // Рассчитываем лайки и дизлайки на основе рейтинга
  // Рейтинг 10 = 100 лайков, 0 дизлайков
  // Рейтинг 5 = 50 лайков, 50 дизлайков
  // Рейтинг 0 = 0 лайков, 100 дизлайков
  const likes = Math.round(rating * 10)
  const dislikes = Math.round((10 - rating) * 10)
  
  return { likes, dislikes }
}

// Голосование за страницу (серверная запись)
const votePage = async (voteType) => {
  const previousVote = userVote.value
  const newVote = previousVote === voteType ? null : voteType
  try {
    const resp = await fetch('http://localhost:3001/api/vote-page', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ movieId: props.id, voteType: newVote, previousVote })
    })
    if (!resp.ok) throw new Error('vote API failed')
    const data = await resp.json()
    pageLikes.value = data.pageLikes
    pageDislikes.value = data.pageDislikes
    userVote.value = newVote

    // Сохраняем локально (опционально)
    if (newVote) localStorage.setItem(`page_vote_${props.id}`, newVote)
    else localStorage.removeItem(`page_vote_${props.id}`)
    localStorage.setItem(`page_ratings_${props.id}`, JSON.stringify({
      likes: pageLikes.value,
      dislikes: pageDislikes.value
    }))

    // Уведомляем другие вкладки/страницы
    window.dispatchEvent(new CustomEvent('ratings-updated', {
      detail: { movieId: props.id, likes: pageLikes.value, dislikes: pageDislikes.value }
    }))
  } catch (error) {
    console.error('Ошибка голосования:', error)
  }
}

// Загрузка комментариев
const loadComments = async () => {
  try {
    // Загружаем комментарии с сервера
    const response = await fetch(`http://localhost:3001/api/movie-comments/${props.id}`)
    
    if (response.ok) {
      const result = await response.json()
      comments.value = result.comments || []
      commentsCount.value = comments.value.length
    } else {
      console.error('Ошибка загрузки комментариев с сервера')
      // Fallback к локальным данным
      if (movie.value && movie.value.comments) {
        comments.value = movie.value.comments
        commentsCount.value = movie.value.comments.length
      } else {
        comments.value = []
        commentsCount.value = 0
      }
    }
  } catch (error) {
    console.error('Ошибка загрузки комментариев:', error)
    // Fallback к локальным данным
    if (movie.value && movie.value.comments) {
      comments.value = movie.value.comments
      commentsCount.value = movie.value.comments.length
    } else {
      comments.value = []
      commentsCount.value = 0
    }
  }
}

// Отправка комментария
const submitComment = async () => {
  try {
    if (!commentForm.value.comment || commentForm.value.comment.length < 50) {
      alert('Комментарий должен содержать минимум 50 знаков')
      return
    }
    
    // Проверяем reCAPTCHA
    let token = null
    if (window.grecaptcha) {
      token = window.grecaptcha.getResponse()
      if (!token) {
        alert('Пожалуйста, подтвердите, что вы не робот.')
        return
      }
    }
    
    // Создаем тело запроса
    const requestBody = {
      movieId: props.id,
      name: commentForm.value.name || 'Гость',
      email: commentForm.value.email,
      comment: commentForm.value.comment,
      'g-recaptcha-response': token,
      parentId: replyToCommentId.value
    }

    // Сохраняем комментарий через API
    const response = await fetch('http://localhost:3001/api/add-comment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok) {
      throw new Error('Ошибка сервера при сохранении комментария')
    }

    const result = await response.json()
    console.log('Комментарий успешно сохранен:', result)
    
    // Очищаем форму и состояние
    commentForm.value.comment = ''
    commentForm.value.name = '' // Опционально, можно сохранять
    commentForm.value.email = '' // Опционально, можно сохранять
    showCaptcha.value = false
    replyToCommentId.value = null

    // Сбрасываем reCAPTCHA
    if (window.grecaptcha) {
      window.grecaptcha.reset()
    }
    
    // Перезагружаем комментарии
    await loadComments()
    
  } catch (error) {
    console.error('Ошибка отправки комментария:', error)
    alert('Ошибка при отправке комментария. ' + error.message)
  }
}

// Установить комментарий для ответа
const replyTo = (commentId) => {
  replyToCommentId.value = commentId
}

// Отменить ответ
const cancelReply = () => {
  replyToCommentId.value = null
}

// Голосование за комментарий
const voteComment = async (commentId, voteType) => {
  try {
    const comment = comments.value.find(c => c.id === commentId)
    if (!comment) return
    
    // Создаем уникальный ключ для localStorage
    const voteKey = `comment_vote_${props.id}_${commentId}`
    
    // Загружаем предыдущий голос пользователя из localStorage
    const previousVote = localStorage.getItem(voteKey)
    const newVote = previousVote === voteType ? null : voteType
    
    // Обновляем рейтинг
    if (previousVote === 'like') comment.rating--
    if (previousVote === 'dislike') comment.rating++
    
    if (newVote === 'like') comment.rating++
    if (newVote === 'dislike') comment.rating--
    
    // Сохраняем новый голос пользователя в localStorage
    if (newVote) {
      localStorage.setItem(voteKey, newVote)
    } else {
      localStorage.removeItem(voteKey)
    }
    
    // Сохраняем голос через API
    try {
      const response = await fetch('http://localhost:3001/api/vote-comment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          movieId: props.id,
          commentId: commentId,
          voteType: newVote,
          previousVote: previousVote
        })
      })

      if (!response.ok) {
        throw new Error('Ошибка сервера при сохранении голоса')
      }

      const result = await response.json()
      // Обновляем рейтинг комментария с серверными данными
      comment.rating = result.comment.rating
      
    } catch (apiError) {
      console.error('Ошибка API при сохранении голоса:', apiError)
      // Откатываем изменения при ошибке
      if (previousVote === 'like') comment.rating--
      if (previousVote === 'dislike') comment.rating++
      
      if (voteType === 'like') comment.rating++
      if (voteType === 'dislike') comment.rating--
      
      comment.userVote = previousVote
      alert('Ошибка при сохранении голоса. Попробуйте еще раз.')
    }
    
  } catch (error) {
    console.error('Ошибка голосования за комментарий:', error)
  }
}

// Показываем капчу при фокусе на поле комментария
const showCaptchaOnFocus = async () => {
  showCaptcha.value = true
  
  // Ждем обновления DOM
  await nextTick()
  
  // Проверяем, есть ли уже reCAPTCHA
  const recaptchaContainer = document.querySelector('.g-recaptcha')
  
  if (recaptchaContainer && window.grecaptcha) {
    // Если reCAPTCHA уже существует, сбрасываем её
    try {
      window.grecaptcha.reset()
    } catch (error) {
      console.log('reCAPTCHA reset error:', error)
      // Если не удалось сбросить, пересоздаем
      await recreateRecaptcha()
    }
  } else if (window.grecaptcha) {
    // Если reCAPTCHA не существует, создаем заново
    await recreateRecaptcha()
  } else {
    // Если grecaptcha не загружен, ждем загрузки
    console.log('reCAPTCHA не загружен, ждем...')
    await waitForRecaptcha()
    await recreateRecaptcha()
  }
}

// Функция для пересоздания reCAPTCHA
const recreateRecaptcha = async () => {
  try {
    // Очищаем старый контейнер
    const oldContainer = document.querySelector('.g-recaptcha')
    if (oldContainer) {
      oldContainer.remove()
    }
    
    // Создаем новый div для reCAPTCHA
    const recaptchaDiv = document.createElement('div')
    recaptchaDiv.className = 'g-recaptcha'
    recaptchaDiv.setAttribute('data-sitekey', '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')
    recaptchaDiv.setAttribute('data-theme', 'light')
    recaptchaDiv.setAttribute('data-language', 'ru')
    
    // Находим контейнер для reCAPTCHA и вставляем новый div
    const recaptchaContainer = document.querySelector('.form__row--protect')
    if (recaptchaContainer) {
      recaptchaContainer.appendChild(recaptchaDiv)
      
      // Рендерим reCAPTCHA
      window.grecaptcha.render(recaptchaDiv, {
        sitekey: '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI',
        theme: 'light',
        language: 'ru'
      })
    }
  } catch (error) {
    console.error('Ошибка инициализации reCAPTCHA:', error)
  }
}

// Функция для получения голоса пользователя за комментарий
const getUserVote = (commentId) => {
  const voteKey = `comment_vote_${props.id}_${commentId}`
  return localStorage.getItem(voteKey)
}

// Функция для ожидания загрузки reCAPTCHA
const waitForRecaptcha = () => {
  return new Promise((resolve) => {
    if (window.grecaptcha) {
      resolve()
      return
    }
    
    const checkInterval = setInterval(() => {
      if (window.grecaptcha) {
        clearInterval(checkInterval)
        resolve()
      }
    }, 100)
    
    // Таймаут через 5 секунд
    setTimeout(() => {
      clearInterval(checkInterval)
      resolve()
    }, 5000)
  })
}

// Инициализация при монтировании
onMounted(() => {
  loadPageRatings()
  loadComments()

  // Загружаем Google reCAPTCHA
  if (!window.grecaptcha) {
    const script = document.createElement('script')
    script.src = 'https://www.google.com/recaptcha/api.js?hl=ru'
    script.async = true
    script.defer = true
    document.head.appendChild(script)
  }

  if (players.value[activeTab.value]?.type === 'sv') {
    ensureCdnVideoHub()
  }

  // Fallback to Player 2 if Player 1 (sv) fails to load
  if (players.value[0]?.type === 'sv') {
    setTimeout(() => {
      if (activeTab.value === 0) {
        const playerContainer = document.getElementById('player_video_0');
        if (!playerContainer) return;

        // Case 1: The iframe is a direct child of the container (or descendant)
        let iframe = playerContainer.querySelector('iframe');

        // Case 2: The iframe is inside the shadow DOM of the <video-player> component
        if (!iframe) {
          const videoPlayerElement = playerContainer.querySelector('video-player');
          if (videoPlayerElement && videoPlayerElement.shadowRoot) {
            iframe = videoPlayerElement.shadowRoot.querySelector('iframe');
          }
        }

        if (!iframe) {
          console.log('Player 1 did not load (iframe not found). Switching to Player 2.');
          activeTab.value = 1;
        }
      }
    }, 5000); // 5 seconds timeout
  }
})

const cdnPlayerLoaded = ref(false)

function ensureCdnVideoHub() {
  if (cdnPlayerLoaded.value) return
  const exists = document.querySelector('script[src*="player.cdnvideohub.com/s2/stable/video-player.umd.js"]')
  if (!exists) {
    const s = document.createElement('script')
    s.src = 'https://player.cdnvideohub.com/s2/stable/video-player.umd.js'
    s.async = true
    s.onload = () => { cdnPlayerLoaded.value = true }
    document.head.appendChild(s)
  } else {
    cdnPlayerLoaded.value = true
  }
}

watch(activeTab, (i) => {
  if (players.value[i]?.type === 'sv') ensureCdnVideoHub()
})

const seoDescription = computed(() => {
  if (!movie.value) return ''
  const title = movie.value.title
  const category = movie.value.category

  // Подстройте список ключей категорий под ваши реальные значения в movies-data.json
  const isSerial = category === 'serialy' || category === 'serials'
  const isAnime = category === 'anime' || category === 'animes'
  const isCartoon = category === 'multfilmy' || category === 'multfilm' || category === 'cartoons'

  if (isSerial) {
    return `На сайте Lordfilms вы можете смотреть ${title} на русском языке бесплатно все сезоны в качестве HD 720p и Full HD 1080p. Начните онлайн просмотр сериала ${title} все серии подряд с русской озвучкой в профессиональном переводе от лучших студий (LostFilm, Кубик в Кубе, NewStudio, ColdFilm, IdeaFilm, Дубляж) или включайте версию с русскими субтитрами. Сериалы на нашем сайте доступны без регистрации и смс. Наш удобный плеер обеспечивает стабильное воспроизведение на любом устройстве: на смартфоне (iOS, Android, Windows Phone), на планшете или Smart TV.`
  } else if (isAnime) {
    return `На сайте Lordfilms вы можете смотреть ${title} на русском языке бесплатно все сезоны в качестве HD 720p и Full HD 1080p. Начните онлайн просмотр аниме ${title} все серии подряд с русской озвучкой в профессиональном переводе от лучших студий (AniLibria, StudioBand, AniDUB, Reanimedia, Студийная банда, Reanimedia) или включайте версию с русскими субтитрами. Аниме на нашем сайте доступны без регистрации и смс. Наш удобный плеер обеспечивает стабильное воспроизведение на любом устройстве: на смартфоне (iOS, Android, Windows Phone), на планшете или Smart TV.`
  } else if (isCartoon) {
    return `На сайте Lordfilms вы можете смотреть ${title} на русском языке бесплатно в качестве HD 720p и Full HD 1080p. Начните онлайн просмотр мультфильма ${title} с русской озвучкой в профессиональном переводе от лучших студий (Мосфильм-Мастер, Пифагор, SDI Media / Blackbird Sound, Невафильм, СВ-Дубль, Amedia, Кириллица, Кравец) или включайте версию с русскими субтитрами. Мультфильмы на нашем сайте доступны без регистрации и смс. Наш удобный плеер обеспечивает стабильное воспроизведение на любом устройстве: на смартфоне (iOS, Android, Windows Phone), на планшете или Smart TV.`
  } else {
    return `На сайте Lordfilms вы можете смотреть ${title} на русском языке бесплатно в качестве HD 720p и Full HD 1080p. Начните онлайн просмотр фильма ${title} с русской озвучкой в профессиональном переводе от лучших студий (Мосфильм-Мастер, Пифагор, SDI Media / Blackbird Sound, Невафильм, СВ-Дубль, Amedia, Кириллица, Кравец) или включайте версию с русскими субтитрами. Фильмы на нашем сайте доступны без регистрации и смс. Наш удобный плеер обеспечивает стабильное воспроизведение на любом устройстве: на смартфоне (iOS, Android, Windows Phone), на планшете или Smart TV.`
  }
})

// Описание: разбиваем по пустым строкам, если нет HTML-версии
const descriptionParagraphs = computed(() => {
  if (!movie.value) return []
  if (movie.value.descriptionHtml) return []
  const text = movie.value.description || ''
  // Разделяем по двойным переводам строк как по абзацам
  return text.split(/\n\s*\n/).map(s => s.trim()).filter(Boolean)
})
</script>

<style scoped>
.no-movie {
  text-align: center;
  padding: 60px 20px;
}

body.light-off {
    overflow: hidden;
}

.light-off-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.85);
    z-index: 9998;
    cursor: pointer;
}

#player-container.player-overlay {
    position: relative;
    z-index: 9999;
    background: #1d1d1d;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 0 25px rgba(0,0,0,0.5);
}

.tabs-block__select button.active {
  background-color: #38be38;
  color: white;
}

.no-movie h1 {
  margin-bottom: 20px;
}

.sv-container { height: 760px; }
@media (max-width: 768px) { .sv-container { height: 300px; } }
@media (max-width: 425px) { .sv-container { height: 200px; } }

.no-movie .btn {
  display: inline-block;
  padding: 12px 24px;
  background: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  margin-top: 20px;
}

/* Стили для оценок */
.page-rate-btn {
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  color: inherit;
}

.page-rate-btn:hover {
  opacity: 0.8;
}
.page-rate-btn.voted .fal {
  transform: scale(1.1);
}

/* Стили для комментариев */
.content-page__comments {
  margin-top: 40px;
}
.comment-item {
  transition: margin-left 0.3s ease-in-out;
}
.comment-form__header {
  gap: 15px;
  margin-bottom: 15px;
}

.comment-form__input {
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.comment-form__input:focus {
  outline: none;
  border-color: #38be38;
  box-shadow: 0 0 0 2px rgba(56, 190, 56, 0.2);
}

.comment-form__editor {
  margin-bottom: 15px;
}

.comment-form__editor textarea {
  width: 100%;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
  min-height: 120px;
}

.comment-form__editor textarea:focus {
  outline: none;
  border-color: #38be38;
  box-shadow: 0 0 0 2px rgba(56, 190, 56, 0.2);
}

.comment-form__btn {
  padding: 12px 24px;
  background: #38be38;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.comment-form__btn:hover:not(:disabled) {
  background: #2ea02e;
}

.comment-form__btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.comment-form__actions {
    display: flex;
    gap: 10px;
}

.cancel-btn {
    background-color: #6c757d;
}

.cancel-btn:hover {
    background-color: #5a6268;
}

.comment {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  background: white;
}

.comment.pos {
  border-left: 4px solid #38be38;
}

.comment.neg {
  border-left: 4px solid #ff6b6b;
}

.comment__header {
  margin-bottom: 15px;
}

.comment__author {
  font-weight: 600;
  color: #333;
}

.comment__date {
  color: #666;
  font-size: 14px;
}

.comment__text {
  line-height: 1.6;
  margin-bottom: 15px;
  color: #333;
}

.comment__tools {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.reply-btn {
  color: #666;
  font-size: 14px;
  cursor: pointer;
  text-decoration: none;
}

.reply-btn:hover {
  text-decoration: underline;
}

.comment__rating {
  display: flex;
  align-items: center;
  gap: 10px;
}
.reply-form-container {
  margin-bottom: 15px;
}
.ratingtypeplusminus {
  font-weight: 600;
  color: #333;
}

.comment__rating-btn {
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: all 0.2s ease;
  text-decoration: none;
}

.comment__rating-btn:hover {
  background: #f5f5f5;
}

.comment__rating-btn.thelike.voted {
  color:rgb(70, 209, 70);
}
.comment__rating-btn.thedislike.voted {
  color: #ff6b6b;
}


.comment__rating-btn.voted .fal {
  transform: scale(1.1);
}

.message-info {
  background: #f8f9fa;
  border-radius: 6px;
  margin-bottom: 20px;
  color: #666;
  text-align: center;
}

.content-page__comments-info {
  padding: 15px;
  background: #e3f2fd;
  border-radius: 6px;
  margin-bottom: 20px;
  color: #1976d2;
  text-align: center;
}
</style>
