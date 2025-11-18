<!-- src/components/Top100Page.vue -->
<template>
  <div class="items-in-grid count-items">
    <section class="sect ignore-select">
      <div class="section--header d-flex ai-center">
        <h1 class="section--title flex-1">Топ-100</h1>
      </div>
      <div class="section--content items-in-grid">
        <MovieCard v-for="movie in items" :key="movie.id" :movie="movie" />
        <div v-if="!items.length && loading" class="tops__loader">Загрузка…</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import MovieCard from './MovieCard.vue'
import { useTopFeed } from '../assets/useTopFeed.js'
import { setMeta, setOg, setCanonical, setTwitter } from '../assets/seoUtils.js'

const itemsRef = useTopFeed(100, 'all')
const items = itemsRef // shallowRef from composable
const loading = ref(false) // simple placeholder, useTopFeed loads on mount

function updateSeo() {
  if (typeof window === 'undefined') return
  const origin = window.location.origin
  const logoAbs = `${origin}/assets/NewLord_site/images/logo.svg`
  const title = 'Топ-100 — лучшие фильмы и сериалы на Lordfilm'
  const desc = 'Топ-100 лучших фильмов и сериалов на Lordfilms по рейтингам и популярности. Смотрите онлайн бесплатно в HD.'
  document.title = title
  setCanonical(origin + '/top-100')
  setMeta('robots', 'index,follow')
  setMeta('description', desc)
  setOg('og:type', 'website')
  setOg('og:title', title)
  setOg('og:description', desc)
  setOg('og:image', logoAbs)
  setOg("og:url", origin + '/top-100')
  setTwitter('twitter:card', 'summary_large_image')
  setTwitter('twitter:title', title)
  setTwitter('twitter:description', desc)
  setTwitter('twitter:image', logoAbs)
}

onMounted(() => {
  updateSeo()
  // Гарантируем, что загрузим именно 100, даже если window.__TOP_FEED__ содержит меньше
  try {
    const need = 100
    const current = Array.isArray(items.value) ? items.value.length : 0
    if (current < need) {
      fetch(`/api/top?limit=${need}&type=all`)
        .then(r => r.ok ? r.json() : Promise.reject())
        .then(j => {
          if (Array.isArray(j.items)) items.value = j.items
        })
        .catch(() => {})
    }
  } catch {}
})
</script>

<style scoped>
.tops__loader {
  width: 100%;
  padding: 40px 0;
  text-align: center;
  color: #666;
  font-size: 16px;
}
</style>
