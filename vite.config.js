import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import purgecss from 'vite-plugin-purgecss';

export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          isCustomElement: (tag) =>
            tag === "video-player" || tag === "video-player-ce",
        },
      },
    }),
    purgecss({
      content: ['./index.html', './src/**/*.vue', './src/**/*.js'],
      safelist: [
        /^owl-/, /^fa-/, /^fal/, /^far/, /^fas/, /^fab/,
        /data-v-.*/,                 // не вырезать scoped‑селекторы
        // сетки:
        /^items-in-grid/, /^items-in-grid__item$/, /^section--content$/,
        // фильтры в CategoryPage:
        /^filters$/, /^filter-select$/, /^section--header$/,
        /^d-flex$/, /^ai-center$/, /^r-gap-20$/, /^c-gap-10$/,
        // плеер MoviePage:
        /^sv-container$/, /^video-responsive$/, /^video-inside$/, /^adaptive-player$/,
        /^player-pane$/, /^player-loader$/, /^player-loader__spinner$/,
        /^pagecontinue---player-.*/, /^tabs-block__content$/
      ],
    }),
  ],
  server: {
    port: 3000,
    watch: {
      ignored: [
        "**/movies-data.json",
        "**/server-data/**",
        "**/uploads/**",
        "**/dist/**",
      ],
    },
  },
  build: {
    cssCodeSplit: true,
    ssrManifest: true,
    rollupOptions: {
      input: { main: "./index.html" },
      output: {
        manualChunks(id) {
          if (id.includes("node_modules")) {
            // не группируем vue и vue-router, они external в SSR
            if (id.includes("/vue") || id.includes("vue-router")) return;
            return "vendor";
          }
        },
      },
    },
  },
});