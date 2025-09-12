<template>
    <div class="page-chunk">
      <MovieCard
        v-for="m in items"
        :key="m.id"
        :movie="m"
      />
    </div>
  </template>
  
  <script setup>
  import MovieCard from './MovieCard.vue'
  
  defineProps({
    items: { type: Array, required: true }
  })
  </script>
  
  <style scoped>
  .page-chunk { display: contents; }
  </style>