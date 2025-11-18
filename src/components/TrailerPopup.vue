<template>
  <Teleport to="body">
    <div 
      v-if="isVisible" 
      class="trl" 
      id="trl"
      @click.self="closeTrailer"
    >
    <div class="youtube-trail-pop__inner">
      <div class="youtube-trail-pop__video video-inside video-responsive">
        <iframe 
          v-if="trailerUrl"
          :src="trailerUrl" 
          frameborder="0" 
          allowfullscreen 
          mozallowfullscreen 
          webkitAllowFullScreen
          loading="lazy"
        ></iframe>
      </div>
      <div class="youtube-trail-pop__content">
        <router-link 
          :to="`/${movie.category}/${movie.id}`" 
          class="youtube-trail-pop__btn btn fal fa-play"
          @click="closeTrailer"
        >
          Смотреть онлайн
        </router-link>
        <div class="blodrich_text" v-html="movie.descriptionHtml || movie.description"></div>
      </div>
    </div>
    <button 
      class="youtube-trail-pop__close btn-nobg btn-square fal fa-times"
      @click="closeTrailer"
    ></button>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, watch } from 'vue'

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  },
  movie: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

// Формируем URL трейлера
const trailerUrl = computed(() => {
  if (!props.movie?.trailer) return null
  
  // Если это YouTube ссылка
  if (props.movie.trailer.includes('youtube.com/watch?v=') || props.movie.trailer.includes('youtu.be/')) {
    const videoId = props.movie.trailer.includes('youtu.be/') 
      ? props.movie.trailer.split('youtu.be/')[1].split('?')[0]
      : props.movie.trailer.split('v=')[1].split('&')[0]
    return `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0`
  }
  
  // Если это Vimeo ссылка
  if (props.movie.trailer.includes('vimeo.com/')) {
    const videoId = props.movie.trailer.split('vimeo.com/')[1].split('?')[0]
    return `https://player.vimeo.com/video/${videoId}?autoplay=1`
  }
  
  // Если это уже готовый embed URL
  return props.movie.trailer
})

const closeTrailer = () => {
  emit('close')
}

// Управление классом body
watch(() => props.isVisible, (newVal) => {
  if (newVal) {
    document.body.classList.add('youtube-trail-pop-opened')
  } else {
    document.body.classList.remove('youtube-trail-pop-opened')
  }
})

// Обработка клавиши Escape
const handleKeydown = (event) => {
  if (event.key === 'Escape' && props.isVisible) {
    closeTrailer()
  }
}

// Добавляем/убираем обработчик клавиатуры
watch(() => props.isVisible, (newVal) => {
  if (newVal) {
    document.addEventListener('keydown', handleKeydown)
  } else {
    document.removeEventListener('keydown', handleKeydown)
  }
})
</script>
