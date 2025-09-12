import { inject, shallowRef, onMounted } from 'vue'

const feed = shallowRef({ popular: [], sections: {} })
let loaded = false

export function useHomeFeed() {
  if (typeof window === 'undefined') {
    const provided = inject('homeFeed', null)
    return shallowRef(provided || { popular: [], sections: {} })
  }
  if (!loaded && window.__HOME_FEED__) {
    feed.value = window.__HOME_FEED__
    loaded = true
  }
  onMounted(async () => {
    if (loaded) return
    try {
      const r = await fetch('/api/home-feed')
      if (r.ok) {
        feed.value = await r.json()
        loaded = true
      }
    } catch {}
  })
  return feed
}