import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

// Импорт компонентов
import HomePage from './components/HomePage.vue'
import CategoryPage from './components/CategoryPage.vue'
import MoviePage from './components/MoviePage.vue'
import Top100Page from './components/Top100Page.vue'
import NotFoundPage from './components/NotFoundPage.vue'

// Настройка маршрутов
const routes = [
  { path: '/', component: HomePage },
  { path: '/filmy', component: CategoryPage, props: { category: 'filmy' } },
  { path: '/serialy', component: CategoryPage, props: { category: 'serialy' } },
  { path: '/multfilmy', component: CategoryPage, props: { category: 'multfilmy' } },
  { path: '/anime', component: CategoryPage, props: { category: 'anime' } },
  { path: '/top100', component: Top100Page },
  { path: '/:category/:id', component: MoviePage, props: true },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: NotFoundPage }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { left: 0, top: 0 }
  }
})

const app = createApp(App)
app.use(router)
app.mount('#app')
