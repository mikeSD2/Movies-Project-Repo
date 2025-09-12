<template>
  <div class="not-found-container">
    <h1>404</h1>
    <h2>Страница не найдена</h2>
    <p>К сожалению, страница, которую вы ищете, не существует.</p>
    <router-link to="/" class="home-link">Вернуться на главную</router-link>
  </div>
</template>

<script>
export default {
  name: 'NotFoundPage'
}
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
  color: var(--tt);
  gap: 12px;
}

h1 {
  font-size: clamp(3rem, 18vw, 8rem);
  line-height: 0.9;
  margin: 0;
  color: var(--green);
}

h2 {
  font-size: clamp(1.4rem, 4vw, 2rem);
  margin: 0;
  font-weight: 500;
  color: var(--tt);
}

p {
  font-size: clamp(1rem, 2.2vw, 1.15rem);
  margin: 0 0 18px 0;
  max-width: 600px;
  color: var(--tt-fade);
}

.home-link {
  padding: 10px 20px;
  background-color: var(--green);
  color: #fff;
  text-decoration: none;
  border-radius: 4px;
  font-weight: 600;
  transition: background-color 0.2s ease, transform 0.1s ease;
  border: 1px solid var(--green);
}

.home-link:hover {
  background-color: #41c24a; /* чуть светлее var(--green) */
  transform: translateY(-1px);
}
</style>