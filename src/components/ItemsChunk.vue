<!-- src/components/ItemsChunk.vue -->
<template>
  <MovieCard
    v-for="m in items"
    :key="m.id"
    :movie="m"
  />
</template>

<script setup>
import MovieCard from './MovieCard.vue'

defineProps({
  items: { type: Array, required: true }
})
</script>