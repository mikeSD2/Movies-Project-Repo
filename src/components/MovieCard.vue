<template>
  <div class="item link-exp_ing items-in-grid__item">
    <div class="assets__img img-block ratio-2-3 img-mask">
      <img
        :src="fallbackSrc"
        :srcset="srcSet"
        :sizes="sizes"
        :alt="movie.title"
        :loading="priority ? 'eager' : 'lazy'"
        decoding="async"
        :fetchpriority="priority ? 'high' : 'auto'"
      >
      <div v-if="movie.season || movie.episode" class="assets__label">{{ [movie.season, movie.episode].filter(Boolean).join(' ') }}</div>
      <div 
        class="assets__btn-info btn btn-square fa-1.3x fal fa-info-circle anim"
        @mouseenter="showTooltip"
        @mouseleave="hideTooltip"
        ref="infoBtn"
      ></div>
    </div>
    <div class="assets__desc d-flex fd-column jc-flex-end img-overlay-icon anim-before fal fa-play">
      <router-link 
        :to="`/${movie.category}/${movie.id}`" 
        class="assets__title link-exp_ing__trg d-block"
      >
        {{ movie.title }}
      </router-link>
      <div class="assets__year">({{ movie.year }})</div>
      
      <div class="assets__rates d-flex jc-space-between">
        <div v-if="movie.kpRating" class="assets__rates-item kp" data-text="KP">
          {{ movie.kpRating }}
        </div>
        <div v-if="movie.imdbRating" class="assets__rates-item imdb" data-text="IMDB">
          {{ formatRating(movie.imdbRating) }}
        </div>
      </div>
    </div>
    
    <!-- Компонент трейлера -->
    <TrailerPopup 
      :is-visible="showTrailerPopup"
      :movie="movie"
      @close="closeTrailerPopup"
    />
  </div>
</template>

<script setup>
import { computed, ref, onUnmounted } from 'vue'
import TrailerPopup from './TrailerPopup.vue'

const props = defineProps({
  movie: { type: Object, required: true },
  priority: { type: Boolean, default: false }
})

function formatRating(val) {
  const n = parseFloat(String(val).replace(',', '.'))
  if (!isFinite(n)) return String(val ?? '')
  const rounded = Math.round(n * 10) / 10
  return Math.abs(rounded - Math.round(rounded)) < 1e-9
    ? String(Math.round(rounded))
    : rounded.toFixed(1)
}

function formatTranslation(val) {
  const MAX = 12;
  const arr = Array.isArray(val) ? val : (val ? [String(val)] : []);
  const cleaned = Array.from(new Set(
    arr
      .flatMap((s) => String(s).split(","))
      .map((s) => s.trim())
      .filter(Boolean)
      .map((s) => s.replace(/\.?Subtitles$/i, "").replace(/\.?TV$/i, ""))
  ));

  const rank = (name) => {
    if (/дубляж|дублирован/i.test(name)) return 900;
    if (/субтит/i.test(name)) return 700;
    const top = ["AniLibria","SHIZA Project","AniDUB","Crunchyroll","Wakanim","AniStar","AnimeVost","Animedia"];
    const i = top.findIndex(t => t.toLowerCase() === name.toLowerCase());
    return i >= 0 ? 800 - i : 100;
  };

  cleaned.sort((a,b) => {
    const da = rank(a), db = rank(b);
    if (db !== da) return db - da;
    return a.localeCompare(b, 'ru');
  });

  return cleaned.slice(0, MAX).join(', ');
}

// Базовый src (фолбэк)
const fallbackSrc = computed(() => {
  if (!props.movie.image) return ''
  if (props.movie.image.startsWith('http')) return props.movie.image
  return `/${props.movie.image}`
})

// sizes оставляем 42vw (порог для 220 ≈ 220/0.42 ≈ 524px при DPR=1)
const sizes = '(min-width:1600px) 260px, (min-width:1366px) 220px, (min-width:1220px) 200px, (min-width:760px) 25vw, 42vw'
const srcSet = computed(() => {
  if (!props.movie.image) return ''
  const rel = props.movie.image.startsWith('http') ? null : `/${props.movie.image}`
  if (!rel) return ''
  const mk = (w) => `/img?src=${encodeURIComponent(rel)}&w=${w}&q=60&f=webp`
  return [
    `${mk(220)} 220w`,
    `${mk(360)} 360w`,
    `${mk(540)} 540w`,
    `${mk(720)} 720w`
  ].join(', ')
})

// Refs
const infoBtn = ref(null)
const tooltipTimer = ref(null)
const showTrailerPopup = ref(false)

// Функция для правильного формирования пути к изображению
const imageSrc = computed(() => {
  if (!props.movie.image) {
    // Можно вернуть путь к картинке-заглушке
    return ''; 
  }
  if (props.movie.image.startsWith('http')) {
    // Если это полная ссылка, возвращаем ее как есть
    return props.movie.image;
  }
  // Иначе, это локальный путь, добавляем слэш
  return `/${props.movie.image}`;
});

// Проверяем есть ли трейлер
const hasTrailer = computed(() => {
  return props.movie.trailer && props.movie.trailer.trim() !== ''
})

// Функции tooltip
const showTooltip = () => {
  if (window.innerWidth <= 1220) return // Только на больших экранах как в оригинале
  
  clearTimeout(tooltipTimer.value)
  
  if (!document.querySelector('.tooltbox') && infoBtn.value) {
    const btnRect = infoBtn.value.getBoundingClientRect()
    const winWidth = window.innerWidth
    let left = btnRect.left + 37
    let top = btnRect.top + window.scrollY
    
    // Если tooltip не помещается справа, показываем слева
    if (left > winWidth / 2 + 200) {
      left = btnRect.left - 457
      document.body.classList.add('pop-left')
    } else {
      document.body.classList.remove('pop-left')
    }
    
    // Создаем tooltip и добавляем к body
    const tooltipEl = document.createElement('div')
    tooltipEl.className = 'tooltbox'
    tooltipEl.style.left = left + 'px'
    tooltipEl.style.top = top + 'px'
    tooltipEl.style.display = 'block'
    
    const seasonEpisode = [props.movie.season, props.movie.episode].filter(Boolean).join(' ')
    const headerSmall = seasonEpisode ? `(${seasonEpisode} | ${props.movie.year})` : `(${props.movie.year})`

    const imdbTxt = props.movie.imdbRating ? formatRating(props.movie.imdbRating) : ''

    tooltipEl.innerHTML = `
      <h1>${props.movie.title} <small>${headerSmall}</small></h1>
      <div class="richtxt">${props.movie.description}</div>
      <ul class="contpage__list">
        ${props.movie.originalTitle ? `<li><span>Название:</span><span>${props.movie.originalTitle}</span></li>` : ''}
        <li><span>Год выхода:</span>${props.movie.year}</li>
        ${props.movie.country ? `<li><span>Страна:</span>${props.movie.country}</li>` : ''}
        ${props.movie.premiere ? `<li><span>Премьера:</span>${props.movie.pремiere}</li>` : ''}
        ${props.movie.director ? `<li><span>Режиссер:</span>${props.movie.director}</li>` : ''}
        ${props.movie.genres && props.movie.genres.length ? `<li><span>Жанр:</span>${props.movie.genres.join(', ')}</li>` : ''}
        ${props.movie.translation ? `<li><span>Перевод:</span>${formatTranslation(props.movie.translation)}</li>` : ''}
        ${props.movie.kpRating || props.movie.imdbRating ? `<li class="contpage__list-rates d-flex ai-center c-gap-20">
          ${props.movie.kpRating ? `<div class="contpage__list-rates-item kp">${props.movie.kpRating}</div>` : ''}
          ${props.movie.imdbRating ? `<div class="contpage__list-rates-item imdb">${imdbTxt}</div>` : ''}
        </li>` : ''}
        ${props.movie.actors ? `<li class="contpage__list-wide"><span>В ролях:</span>${props.movie.actors}</li>` : ''}
      </ul>
      ${hasTrailer.value ? `<button class="contpage__btn-trailer js-show-trailer">Смотреть трейлер</button>` : ''}
    `
    
    // Добавляем обработчики событий
    tooltipEl.addEventListener('mouseenter', clearTooltipTimer)
    tooltipEl.addEventListener('mouseleave', hideTooltip)
    
    // Добавляем обработчик для кнопки трейлера
    const trailerBtn = tooltipEl.querySelector('.js-show-trailer')
    if (trailerBtn) {
      trailerBtn.addEventListener('click', showTrailer)
    }
    
    document.body.appendChild(tooltipEl)
  }
}

const hideTooltip = () => {
  tooltipTimer.value = setTimeout(() => {
    const tooltip = document.querySelector('.tooltbox')
    if (tooltip) {
      tooltip.remove()
    }
    document.body.classList.remove('pop-left')
  }, 100)
}

const clearTooltipTimer = () => {
  clearTimeout(tooltipTimer.value)
}

const showTrailer = () => {
  // Скрываем tooltip при показе трейлера
  const tooltip = document.querySelector('.tooltbox')
  if (tooltip) {
    tooltip.remove()
  }
  document.body.classList.remove('pop-left')
  
  // Показываем трейлер
  showTrailerPopup.value = true
}

const closeTrailerPopup = () => {
  showTrailerPopup.value = false
}

// Очистка при размонтировании
onUnmounted(() => {
  clearTimeout(tooltipTimer.value)
  const tooltip = document.querySelector('.tooltbox')
  if (tooltip) {
    tooltip.remove()
  }
  document.body.classList.remove('pop-left')
})
</script>
