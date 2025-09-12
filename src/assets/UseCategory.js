// src/assets/useCategory.js
import { ref, watchEffect } from 'vue';

export function useCategory(paramsRef) {
  const state = ref({ items: [], page: 1, total: 0, totalPages: 1 });
  watchEffect(async () => {
    const p = paramsRef.value;
    const qs = new URLSearchParams(p).toString();
    const r = await fetch(`/api/movies?${qs}`);
    state.value = r.ok ? await r.json() : { items: [], page: 1, total: 0, totalPages: 1 };
  });
  return state;
}