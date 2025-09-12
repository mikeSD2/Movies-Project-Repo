import { createApp as _createApp, createSSRApp } from 'vue'
import { createRouter, createWebHistory, createMemoryHistory } from 'vue-router'
import App from './App.vue'
import HomePage from './components/HomePage.vue'

const routes = [
  { path: '/', component: HomePage },
  { path: '/filmy', component: () => import('./components/CategoryPage.vue'), props: { category: 'filmy' } },
  { path: '/serialy', component: () => import('./components/CategoryPage.vue'), props: { category: 'serialy' } },
  { path: '/multfilmy', component: () => import('./components/CategoryPage.vue'), props: { category: 'multfilmy' } },
  { path: '/anime', component: () => import('./components/CategoryPage.vue'), props: { category: 'anime' } },
  { path: '/tops', component: () => import('./components/TopsPage.vue') },
  { path: '/:category/:id', component: () => import('./components/MoviePage.vue'), props: true },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('./components/NotFoundPage.vue') }
]

export function createApp(isServer = false, url = '/') {
  const history = isServer ? createMemoryHistory() : createWebHistory()
  const router = createRouter({
    history,
    routes,
    scrollBehavior() { return { left: 0, top: 0 } }
  })
  const app = (isServer ? createSSRApp : _createApp)(App)
  app.use(router)

  if (!isServer) {
    router.beforeResolve(async (to, from, next) => {
      try {
        const parts = to.path.split('/').filter(Boolean)
        // Главная
        if (to.path === '/') {
          if (!window.__HOME_FEED__) {
            const r = await fetch('/api/home-feed')
            if (r.ok) window.__HOME_FEED__ = await r.json()
          }
        }
        // Топы
        else if (to.path === '/tops') {
          const t = String(to.query.type || 'all')
          const r = await fetch(`/api/top?type=${encodeURIComponent(t)}&limit=24&offset=0`)
          if (r.ok) {
            const j = await r.json()
            window.__TOP_FEED__ = {
              items: j.items,
              total: j.total,
              limit: 24,
              offset: 0,
              type: t
            }
          }
        }
        // Категории
        else if (parts.length === 1 && ['filmy','serialy','multfilmy','anime'].includes(parts[0])) {
          const name = parts[0]
          const params = new URLSearchParams({
            name,
            page: String(to.query.page || 1),
            limit: String(to.query.limit || 24),
            sort: String(to.query.sort || 'year')
          })
          if (to.query.year) params.set('year', String(to.query.year))
          if (to.query.genre) params.set('genre', String(to.query.genre))
          if (to.query.country) params.set('country', String(to.query.country))
          if (to.query.translation) params.set('translation', String(to.query.translation))
          if (to.query.actor) params.set('actor', String(to.query.actor))
          if (to.query.special) params.set('special', String(to.query.special))

          const r = await fetch(`/api/category?${params.toString()}`)
          if (r.ok) {
            const data = await r.json()
            window.__CATEGORY_FEED__ = window.__CATEGORY_FEED__ || {}
            // Кэш по слагу (как ожидает компонент)
            window.__CATEGORY_FEED__[name] = data
          }
        }
        // Страница фильма
        else if (parts.length === 2) {
          const id = parts[1]
          const r = await fetch(`/api/movie-full/${encodeURIComponent(id)}`)
          if (r.ok) {
            const payload = await r.json()
            window.__MOVIE_PAYLOAD__ = payload
          }
        }
      } catch (_) {
        // молча fallback-им
      } finally {
        next()
      }
    })
  }

  return { app, router }
}