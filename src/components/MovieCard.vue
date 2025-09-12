<template>
  <div class="item link-exp_ing grid-items__item">
    <div class="media__img img-block ratio-2-3 img-mask">
      <img :src="imageSrc" :alt="movie.title" loading="lazy">
      <div v-if="movie.season" class="media__label">{{ movie.season }}</div>
      <div 
        class="media__btn-info btn btn-square fa-1.3x fal fa-info-circle anim"
        @mouseenter="showTooltip"
        @mouseleave="hideTooltip"
        ref="infoBtn"
      ></div>
    </div>
    <div class="media__desc d-flex fd-column jc-flex-end img-overlay-icon anim-before fal fa-play">
      <router-link 
        :to="`/${movie.category}/${movie.id}`" 
        class="media__title link-exp_ing__trg d-block"
      >
        {{ movie.title }}
      </router-link>
      <div class="media__year">({{ movie.year }})</div>
      
      <div class="media__rates d-flex jc-space-between">
        <div v-if="movie.kpRating" class="media__rates-item kp" data-text="KP">
          {{ movie.kpRating }}
        </div>
        <div v-if="movie.imdbRating" class="media__rates-item imdb" data-text="IMDB">
          {{ movie.imdbRating }}
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
  movie: {
    type: Object,
    required: true
  }
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
  
  if (!document.querySelector('.tooltip-box') && infoBtn.value) {
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
    tooltipEl.className = 'tooltip-box'
    tooltipEl.style.left = left + 'px'
    tooltipEl.style.top = top + 'px'
    tooltipEl.style.display = 'block'
    
    tooltipEl.innerHTML = `
      <h1>${props.movie.title} <small>${props.movie.season ? `(${props.movie.season} | ${props.movie.year})` : `(${props.movie.year})`}</small></h1>
      <div class="rich-text">${props.movie.description}</div>
      <ul class="content-page__list">
        ${props.movie.originalTitle ? `<li><span>Название:</span><span>${props.movie.originalTitle}</span></li>` : ''}
        <li><span>Год выхода:</span>${props.movie.year}</li>
        ${props.movie.country ? `<li><span>Страна:</span>${props.movie.country}</li>` : ''}
        ${props.movie.premiere ? `<li><span>Премьера:</span>${props.movie.premiere}</li>` : ''}
        ${props.movie.director ? `<li><span>Режиссер:</span>${props.movie.director}</li>` : ''}
        ${props.movie.genres && props.movie.genres.length ? `<li><span>Жанр:</span>${props.movie.genres.join(', ')}</li>` : ''}
        ${props.movie.translation ? `<li><span>Перевод:</span>${props.movie.translation}</li>` : ''}
        ${props.movie.ageRating ? `<li><span>Возраст:</span>${props.movie.ageRating}</li>` : ''}
        ${props.movie.kpRating || props.movie.imdbRating ? `<li class="content-page__list-rates d-flex ai-center c-gap-20">
          ${props.movie.kpRating ? `<div class="content-page__list-rates-item kp">${props.movie.kpRating}</div>` : ''}
          ${props.movie.imdbRating ? `<div class="content-page__list-rates-item imdb">${props.movie.imdbRating}</div>` : ''}
        </li>` : ''}
        ${props.movie.actors ? `<li class="content-page__list-wide"><span>В ролях:</span>${props.movie.actors}</li>` : ''}
      </ul>
      ${hasTrailer.value ? `<button class="content-page__btn-trailer js-show-trailer">Смотреть трейлер</button>` : ''}
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
    const tooltip = document.querySelector('.tooltip-box')
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
  const tooltip = document.querySelector('.tooltip-box')
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
  const tooltip = document.querySelector('.tooltip-box')
  if (tooltip) {
    tooltip.remove()
  }
  document.body.classList.remove('pop-left')
})
</script>
