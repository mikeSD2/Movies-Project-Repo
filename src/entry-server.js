import { createApp } from './app'
import { renderToString } from 'vue/server-renderer'

export async function render(url, initialState = {}) {
  const { app, router } = createApp(true, url)

  if (initialState.homeFeed) {
    app.provide('homeFeed', initialState.homeFeed)
  }
  if (initialState.topFeed) {
    app.provide('topFeed', {
      type: initialState.topFeed.type,
      limit: initialState.topFeed.limit,
      offset: initialState.topFeed.offset,
      items: initialState.topFeed.data.items,
      total: initialState.topFeed.data.total,
    })
  }
  if (initialState.categoryFeed) {
    app.provide('categoryFeed', initialState.categoryFeed.feed)
  }
  if (initialState.moviePayload) {
    app.provide('moviePayload', initialState.moviePayload)
  }

  await router.push(url)
  await router.isReady()

  const ctx = { initialState }
  const html = await renderToString(app, ctx)
  return { html, ctx }
}