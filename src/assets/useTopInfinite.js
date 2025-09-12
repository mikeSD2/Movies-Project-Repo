import { shallowRef, ref } from "vue"

const cache = new Map()

export function useTopInfinite(initial = null) {
  const items = shallowRef([])
  const total = ref(0)
  const limit = ref(24)
  const offset = ref(0)
  const type = ref('all')
  const loading = ref(false)
  const error = ref(null)

  const controller = ref(null)
  let reqId = 0

  function hydrateSnapshot(raw, t = type.value) {
    if (!raw) return
    const snapshot = {
      items: Array.isArray(raw.items) ? [...raw.items] : [],
      total: raw.total || 0,
      offset: raw.offset ?? (Array.isArray(raw.items) ? raw.items.length : 0),
      limit: raw.limit || limit.value,
      fullyLoaded:
        (raw.items?.length || 0) >= (raw.total || 0) ||
        (raw.items?.length || 0) < (raw.limit || limit.value),
    }
    cache.set(t, snapshot)
    if (t === type.value) applySnapshot(snapshot)
    limit.value = snapshot.limit
  }

  function applySnapshot(snapshot) {
    if (!snapshot) return
    items.value = [...snapshot.items]
    total.value = snapshot.total || 0
    offset.value = snapshot.offset || items.value.length
    limit.value = snapshot.limit || limit.value
  }

  function ensureSnapshot(t) {
    if (!cache.has(t)) {
      cache.set(t, {
        items: [],
        total: 0,
        offset: 0,
        limit: limit.value,
        fullyLoaded: false,
      })
    }
    return cache.get(t)
  }

  // SSR / переданное начальное состояние
  if (typeof window !== 'undefined' && window.__TOP_FEED__) {
    const ssr = window.__TOP_FEED__
    type.value = ssr.type || 'all'
    hydrateSnapshot(
      {
        items: ssr.items || [],
        total: ssr.total || 0,
        offset: ssr.offset || (ssr.items ? ssr.items.length : 0),
        limit: ssr.limit || 24,
      },
      type.value
    )
  } else if (initial && Array.isArray(initial.items)) {
    hydrateSnapshot(initial)
  }

  const hasMore = () => {
    const snapshot = cache.get(type.value)
    if (snapshot?.fullyLoaded) return false
    return items.value.length < total.value
  }

  async function fetchPage(nextOffset, t = type.value) {
    try {
      controller.value?.abort()
    } catch {}

    const myController = new AbortController()
    controller.value = myController
    const myReqId = ++reqId

    loading.value = true
    error.value = null

    try {
      const url = `/api/top?limit=${limit.value}&offset=${nextOffset}&type=${encodeURIComponent(
        t
      )}`
      const resp = await fetch(url, { signal: myController.signal })
      if (!resp.ok) throw new Error('top-fetch-failed')

      const data = await resp.json() // { items, total }
      if (myReqId !== reqId) return // пришёл устаревший ответ

      const snapshot = ensureSnapshot(t)
      const incoming = Array.isArray(data.items) ? data.items : []

      const mergedItems =
        nextOffset === 0 ? incoming : snapshot.items.concat(incoming)

      const totalCount =
        typeof data.total === 'number'
          ? data.total
          : snapshot.total || mergedItems.length

      const updatedSnapshot = {
        items: mergedItems,
        total: totalCount,
        offset: mergedItems.length,
        limit: limit.value,
        fullyLoaded:
          mergedItems.length >= totalCount || incoming.length < limit.value,
      }

      cache.set(t, updatedSnapshot)
      if (type.value === t) applySnapshot(updatedSnapshot)
    } catch (err) {
      if (err?.name === 'AbortError') return
      error.value = err
    } finally {
      if (myReqId === reqId) loading.value = false
    }
  }

  async function loadMore() {
    if (loading.value) return
    const snapshot = cache.get(type.value)
    if (snapshot?.fullyLoaded) return
    if (!hasMore()) return
    await fetchPage(offset.value, type.value)
  }

  async function setType(newType) {
    const next = newType || 'all'
    if (type.value === next && items.value.length) return

    type.value = next
    const snapshot = cache.get(next)
    if (snapshot) {
      applySnapshot(snapshot)
      return
    }

    items.value = []
    total.value = 0
    offset.value = 0

    await fetchPage(0, next)
  }

  if (
    typeof window !== 'undefined' &&
    items.value.length === 0 &&
    !loading.value
  ) {
    fetchPage(0, type.value)
  }

  return {
    items,
    total,
    hasMore,
    loading,
    error,
    loadMore,
    setType,
    type,
  }
}