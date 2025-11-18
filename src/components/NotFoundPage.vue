<template>
  <div class="not-found-container">
    <h1>404</h1>
    <h2>Страница не найдена</h2>
    <p>К сожалению, страница, которую вы ищете, не существует.</p>
    <router-link to="/" class="home-link">Вернуться на главную</router-link>
  </div>
</template>

<script setup>
import { onMounted } from "vue"
import { setMeta, setCanonical } from "../assets/seoUtils.js"

defineOptions({ name: "NotFoundPage" })

onMounted(() => {
  if (typeof window === "undefined") return
  const origin = window.location.origin
  const url = origin + window.location.pathname
  document.title = "Страница не найдена — Lordfilm"
  setMeta("description", "Страница не найдена.")
  setMeta("robots", "noindex,follow")
  setCanonical(url)
})
</script>

<style scoped>
.not-found-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  text-align: center;
  padding: 20px;
  background: none;
  color: var(--the-tt);
  gap: 12px;
}

h1 {
  font-size: clamp(3rem, 18vw, 8rem);
  line-height: 0.9;
  margin: 0;
  color: var(--clr-green);
}

h2 {
  font-size: clamp(1.4rem, 4vw, 2rem);
  margin: 0;
  font-weight: 500;
  color: var(--the-tt);
}

p {
  font-size: clamp(1rem, 2.2vw, 1.15rem);
  margin: 0 0 18px 0;
  max-width: 600px;
  color: var(--the-tt-fade);
}

.home-link {
  padding: 10px 20px;
  background-color: var(--clr-green);
  color: #fff;
  text-decoration: none;
  border-radius: 4px;
  font-weight: 600;
  transition: background-color 0.2s ease, transform 0.1s ease;
  border: 1px solid var(--clr-green);
}

.home-link:hover {
  background-color: #41c24a; /* чуть светлее var(--clr-green) */
  transform: translateY(-1px);
}
</style>
