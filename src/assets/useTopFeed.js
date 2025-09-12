import { inject, shallowRef, onMounted } from 'vue'

export function useTopFeed(limit = 100, type = 'all') {
  if (typeof window === 'undefined') {
    const provided = inject('topFeed', null)
    return shallowRef(provided || [])
  }
  const state = shallowRef([])
  if (window.__TOP_FEED__?.items) state.value = window.__TOP_FEED__.items
  onMounted(async () => {
    if (state.value?.length) return
    try {
      const r = await fetch(`/api/top?limit=${limit}&type=${encodeURIComponent(type)}`)
      if (r.ok) {
        const j = await r.json()
        state.value = j.items || []
      }
    } catch {}
  })
  return state
}