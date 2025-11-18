<template>
  <div
    v-if="isLightOff"
    class="light-off-overlay"
    @click="isLightOff = false"
  ></div>
  <div v-if="movie" class="panel-of-speed ws-nowrap">
    <router-link to="/">Lordfilms</router-link> »
    <router-link :to="`/${movie.category}`">{{ categoryTitle }}</router-link> »
    {{ movie.title }}
  </div>

  <div class="items-in-grid count-items">
    <article v-if="movie && !isLoading" class="page ignore-select">
      <div class="pagecontinue---bg">
        <div class="pagecontinue---cols">
          <div class="pagecontinue---cols-left">
            <div class="pagecontinue---main" :class="{ 'is-narrow-poster': isSmallPoster }">
              <div class="pagecontinue---header">
                <h1>
                  {{ movie.title }}
                  <small>{{ h1Text }}</small>
                </h1>
                <!--Подсказка: кликните по жанрам или странам ниже, чтобы найти похожие фильмы.-->
              </div>

              <div class="pagecontinue---poster">
                <div class="pagecontinue---img img-block ratio-2-3 img-mask" :class="{ 'is-narrow': isSmallPoster }">
                  <img
                    :alt="movie.title"
                    :src="imageUrl"
                    :srcset="posterSrcset"
                    :sizes="posterSizes"
                    loading="eager"
                    fetchpriority="high"
                    decoding="async"
                  />
                  <div
                    v-if="movie.season || movie.episode"
                    class="assets__label"
                  >
                    {{
                      [movie.season, movie.episode].filter(Boolean).join(" ")
                    }}
                  </div>
                </div>
                <div
                  class="pagecontinue---ext-rating d-flex ai-center jc-space-between"
                >
                  <div
                    class="pagecontinue---ratingscore-ring pi-center p-relative bdrs-50 ratio-1-1"
                    style="--p: 100%"
                  >
                    {{ calculatedRating }}
                  </div>
                  <a
                    class="page-rate-btn"
                    :class="{
                      voted: userVote === 'like',
                      'is-disabled': isVotingDisabled,
                    }"
                    :aria-disabled="isVotingDisabled"
                    data-vote-type="like"
                    href="#"
                    @click.prevent="votePage('like')"
                  >
                    <span class="fal fa-thumbs-up"></span>
                    <span class="page-likes-count">{{ pageLikes }}</span>
                  </a>
                  <a
                    class="page-rate-btn"
                    :class="{
                      voted: userVote === 'dislike',
                      'is-disabled': isVotingPage,
                    }"
                    :aria-disabled="isVotingPage"
                    data-vote-type="dislike"
                    href="#"
                    @click.prevent="votePage('dislike')"
                  >
                    <span class="page-dislikes-count">{{ pageDislikes }}</span>
                    <span class="fal fa-thumbs-down"></span>
                  </a>
                </div>
              </div>

              <div class="pagecontinue---info">
                <div class="pagecontinue---text p-relative clearfix">
                  <div
                    ref="descrScrollRef"
                    :class="[
                      { 'js-hide-text': !isDescriptionExpanded && canExpand },
                    ]"
                    :style="
                      !isDescriptionExpanded && canExpand
                        ? 'padding-bottom: 38px'
                        : ''
                    "
                  >
                    <div
                      ref="descrContentRef"
                      class="blodrich_text p-relative movie-descr"
                    >
                      <div
                        v-if="movie.descriptionHtml"
                        v-html="movie.descriptionHtml"
                      ></div>
                      <template v-else>
                        <p v-for="(p, i) in descriptionParagraphs" :key="i">
                          {{ p }}
                        </p>
                      </template>
                    </div>
                  </div>

                  <!-- Кнопка поверх, не прокручивается -->
                  <button
                    v-show="
                      !isDescriptionExpanded &&
                      (hasMeasured ? canExpand : initialCanExpand)
                    "
                    class="show-text"
                    type="button"
                    @click="isDescriptionExpanded = true"
                  >
                    Развернуть описание
                  </button>
                </div>

                <!-- Кнопка сворачивания — отдельной строкой -->
                <!-- <button
                  v-show="isDescriptionExpanded && (hasMeasured ? canExpand : initialCanExpand)"
                  class="btn-border btn-smaller"
                  type="button"
                  @click="isDescriptionExpanded = false"
                  style="margin-top: 8px"
                >
                  Свернуть описание
                </button> -->

                <ul class="pagecontinue---list">
                  <li v-if="movie.originalTitle">
                    <span>Название:</span>
                    <span>{{ movie.originalTitle }}</span>
                  </li>
                  <li>
                    <span>Год выхода:</span
                    ><router-link
                      :to="`/${movie.category}?year=${movie.year}`"
                      >{{ movie.year }}</router-link
                    >
                  </li>
                  <li v-if="movie.country">
                    <span>Страна:</span>
                    <template
                      v-for="(country, index) in countriesList"
                      :key="country"
                    >
                      <router-link
                        :to="`/${movie.category}?country=${encodeURIComponent(
                          country
                        )}`"
                        >{{ country }}</router-link
                      ><span v-if="index < countriesList.length - 1">, </span>
                    </template>
                  </li>
                  <li v-if="movie.premiere">
                    <span>Премьера:</span>{{ movie.premiere }}
                  </li>
                  <li v-if="movie.director">
                    <span>Режиссер:</span>{{ movie.director }}
                  </li>
                  <li v-if="movie.genres && movie.genres.length">
                    <span>Жанр:</span>
                    <template
                      v-for="(genre, index) in movie.genres"
                      :key="genre"
                    >
                      <router-link
                        :to="`/${movie.category}?genre=${encodeURIComponent(
                          genre
                        )}`"
                        >{{ genre }}</router-link
                      ><span v-if="index < movie.genres.length - 1">, </span>
                    </template>
                  </li>
                  <li v-if="translationsList.length">
                    <span>Перевод:</span>
                    <template v-for="(tr, index) in translationsList" :key="tr">
                      <router-link
                        :to="`/${
                          movie.category
                        }?translation=${encodeURIComponent(tr)}`"
                        >{{ tr }}</router-link
                      ><span v-if="index < translationsList.length - 1"
                        >,
                      </span>
                    </template>
                  </li>
                  <li v-if="movie.ageRating">
                    <span>Возраст:</span>{{ movie.ageRating }}
                  </li>
                  <li
                    v-if="movie.kpRating || movie.imdbRating"
                    class="pagecontinue---list-rates d-flex ai-center c-gap-20"
                  >
                    <div
                      v-if="movie.kpRating"
                      class="pagecontinue---list-rates-item kp"
                    >
                      {{ movie.kpRating }}
                    </div>
                    <div
                      v-if="movie.imdbRating"
                      class="pagecontinue---list-rates-item imdb"
                    >
                      {{ formatRating(movie.imdbRating) }}
                    </div>
                  </li>
                  <li v-if="movie.actors" class="pagecontinue---list-wide">
                    <span>В ролях:</span>
                    <template v-for="(actor, index) in actorsListLimited" :key="actor">
                      <span class="actor-name">{{ actor }}</span><span v-if="index < actorsListLimited.length - 1">, </span>
                    </template>
                    <span v-if="actorsList.length > actorsListLimited.length"> и другие</span>
                  </li>
                </ul>
              </div>
            </div>

            <h2 class="pagecontinue---subtitle">
              {{ h2Text }}
            </h2>
          </div>
        </div>

        <!-- Плеер -->
        <div class="pagecontinue---cols">
          <div
            class="pagecontinue---cols-left pagecontinue---player tabs-block nl"
            id="player-container"
            :class="{ 'player-overlay': isLightOff }"
          >
            <div class="pagecontinue---player-controls d-flex ai-center p-relative">
              <!--Совет: если плеер не запускается — переключите вкладку «Плеер 1/2/3».-->
              <div
                class="tabs-block__select d-flex flex-1"
                v-if="hasWorkingPlayer"
              >
                <template v-for="(player, index) in players" :key="index">
                  <button
                    v-if="index === 0 || !failedPlayers[index]"
                    :class="{ active: activeTab === index }"
                    @click="activeTab = index"
                  >
                    {{ player.name }}
                  </button>
                </template>
              </div>
              <div
                class="pagecontinue---complaint d-flex ai-center jc-space-between c-gap-20"
              >
                <label class="pagecontinue---light-button has-checkbox" for="light">
                  <input
                    id="light"
                    name="light"
                    type="checkbox"
                    v-model="isLightOff"
                  />
                  <span>Свет</span>
                </label>
              </div>
            </div>

            <div
              class="tabs-block__content video-inside"
              v-if="hasWorkingPlayer"
            >
              <template v-for="(player, index) in players" :key="index">
                <div
                  v-if="index === 0 || !failedPlayers[index]"
                  v-show="activeTab === index"
                  class="player-pane"
                >
                  <!-- <div v-if="!playerReady[index]" class="player-loader">
                    <div class="player-loader__spinner"></div>
                    <span>Загружаем плеер…</span>
                  </div> -->
                  <div
                    v-if="player.type === 'sv'"
                    :id="`player_video_${index}`"
                    class="sv-container"
                  >
                    <video-player
                      :id="`cdnvideohubvideoplayer_${index}`"
                      data-publisher-id="79"
                      :data-title-id="String(player.kinopoiskId)"
                      data-aggregator="kp"
                      is-show-banner="false"
                    />
                  </div>
                  <div
                    v-else-if="player.type === 'iframe'"
                    class="video-responsive video-inside adaptive-player"
                  >
                    <iframe
                      :src="player.src"
                      frameborder="0"
                      scrolling="no"
                      allowfullscreen
                      width="800"
                      height="452"
                      referrerpolicy="no-referrer-when-downgrade"
                      loading="lazy"
                      :ref="(el) => registerIframeRef(index, el)"
                      @load="handleIframeLoad(index)"
                      @error="handleIframeError(index)"
                    ></iframe>
                  </div>
                  <div
                    v-else-if="player.type === 'kodik'"
                    id="kodik-player"
                    class="video-responsive video-inside has-12345 adaptive-player"
                  ></div>
                  <div
                    v-else-if="player.type === 'youtube'"
                    class="video-responsive video-inside has-12345"
                  >
                    <iframe
                      allowfullscreen
                      frameborder="0"
                      loading="lazy"
                      :src="player.src"
                      @load="handleYoutubeLoad(index)"
                    ></iframe>
                  </div>
                </div>
              </template>
            </div>

            <div v-else class="video-fallback">
              <span
                class="fal fa-video-slash"
                style="font-size: 48px; margin-bottom: 20px"
              ></span>
              <p>
                Это страница-анонса. Мы уже работаем над тем, чтобы добавить «{{
                  movie.title
                }}» для просмотра. Фильм станет доступен в ближайшее время.
              </p>
            </div>

            <div
              class="pagecontinue---player-bottom d-flex ai-center jc-space-between r-gap-20 c-gap-20"
            >
              <div class="pagecontinue---fav p-relative ml-auto"></div>
              <div class="pagecontinue---likes d-flex fa-inside-1.3x">
                <a
                  class="page-rate-btn"
                  :class="{
                    voted: userVote === 'like',
                    'is-disabled': isVotingPage,
                  }"
                  :aria-disabled="isVotingPage"
                  data-vote-type="like"
                  href="#"
                  @click.prevent="votePage('like')"
                >
                  <span class="fal fa-thumbs-up"></span>
                  <span class="page-likes-count">{{ pageLikes }}</span>
                </a>
                <a
                  class="page-rate-btn"
                  :class="{
                    voted: userVote === 'dislike',
                    'is-disabled': isVotingPage,
                  }"
                  :aria-disabled="isVotingPage"
                  data-vote-type="dislike"
                  href="#"
                  @click.prevent="votePage('dislike')"
                >
                  <span class="page-dislikes-count">{{ pageDislikes }}</span>
                  <span class="fal fa-thumbs-down"></span>
                </a>
              </div>
            </div>
          </div>
        </div>

        <!-- Комментарии -->
        <div class="pagecontinue---cols">
          <div class="pagecontinue---cols-left">
            <div class="pagecontinue---comments">
              <div class="section--title">Комментарии ({{ commentsCount }})</div>
              <div class="pagecontinue---comments-info fal fa-exclamation-circle">
                Минимальная длина комментария - 50 знаков. Комментарии
                модерируются
              </div>

              <!-- Main Comment Form Container -->
              <div
                v-if="!replyToCommentId"
                class="pagecontinue---ac"
                id="main-the_comment-form"
              >
                <form id="dle-comments-form" @submit.prevent="submitComment">
                  <div
                    class="the_comment-form serv form ignore-select comment-toggle"
                  >
                    <div class="form_for-comment--header d-flex ai-center">
                      <input
                        class="form_for-comment--input flex-grow-1"
                        id="name"
                        maxlength="35"
                        name="name"
                        placeholder="Ваше имя"
                        type="text"
                        v-model="commentForm.name"
                        required
                      />
                      <input
                        class="form_for-comment--input flex-grow-1"
                        id="mail"
                        maxlength="35"
                        name="mail"
                        placeholder="Ваш e-mail (необязательно)"
                        type="text"
                        v-model="commentForm.email"
                      />
                    </div>
                    <div class="form_for-comment--editor p-relative">
                      <div class="bb-editor">
                        <textarea
                          cols="70"
                          id="comments"
                          name="comments"
                          rows="10"
                          placeholder="Ваш комментарий..."
                          v-model="commentForm.comment"
                          @focus="showCaptchaOnFocus"
                          required
                        ></textarea>
                      </div>
                    </div>
                    <div
                      class="message-info form"
                      :class="{ 'd-none': !showCaptcha }"
                    >
                      <div class="form__row form__row--protect">
                        <label class="form__label form__label--important" for=""
                          >Защита от спама</label
                        >
                        <div
                          class="g-recaptcha"
                          data-language="ru"
                          data-sitekey="6LeMNBgsAAAAAF-cI33csG6ZC9_BKo6x-ljo7yZN"
                          data-theme="light"
                        ></div>
                      </div>
                    </div>
                    <button
                      class="form_for-comment--btn"
                      name="submit"
                      type="submit"
                      :disabled="
                        !commentForm.comment || commentForm.comment.length < 50
                      "
                    >
                      Отправить
                    </button>
                  </div>
                  <input name="subaction" type="hidden" value="addcomment" />
                  <input
                    id="post_id"
                    name="post_id"
                    type="hidden"
                    :value="movie?.id"
                  />
                </form>
              </div>

              <div v-if="comments.length === 0" class="message-info">
                Комментариев еще нет. Вы можете стать первым!
              </div>
              <div class="pagecontinue---comments-list" id="pagecontinue---comments-list">
                <div id="dle-ajax-comments">
                  <div
                    v-for="comment in processedComments"
                    :key="comment.id"
                    class="comment-item"
                    :style="{ 'margin-left': comment.level * 30 + 'px' }"
                  >
                    <div
                      class="comment js-comm"
                      :class="{
                        pos: comment.rating > 0,
                        neg: comment.rating < 0,
                      }"
                    >
                      <div
                        class="coment__header d-flex ai-center jc-space-between"
                      >
                        <div class="coment__author">{{ comment.name }}</div>
                        <div class="coment__date">{{ comment.date }}</div>
                      </div>
                      <div class="coment__text">{{ comment.comment }}</div>
                      <div class="coment__tools">
                        <div
                          class="ratingsOnComment"
                          :data-comment-id="comment.id"
                        >
                          <span class="ratingtypeplusminus">{{
                            comment.rating > 0
                              ? "+" + comment.rating
                              : comment.rating
                          }}</span>
                          <a
                            class="ratingsOnComment-btn thelike"
                            href="#"
                            @click.prevent="voteComment(comment.id, 'like')"
                            :class="{
                              voted: getUserVote(comment.id) === 'like',
                              'is-disabled': isCommentLocked(comment.id),
                            }"
                          >
                            <span class="fal fa-thumbs-up"></span>
                          </a>
                          <a
                            class="ratingsOnComment-btn thedislike"
                            href="#"
                            @click.prevent="voteComment(comment.id, 'dislike')"
                            :class="{
                              voted: getUserVote(comment.id) === 'dislike',
                              'is-disabled': isCommentLocked(comment.id),
                            }"
                          >
                            <span class="fal fa-thumbs-down"></span>
                          </a>
                        </div>
                        <a
                          href="#"
                          class="reply-btn"
                          @click.prevent="replyTo(comment.id)"
                          >Ответить</a
                        >
                      </div>
                    </div>

                    <!-- Reply Form Container -->
                    <div
                      v-if="replyToCommentId === comment.id"
                      class="reply-form-container"
                    >
                      <form
                        id="dle-comments-form-reply"
                        @submit.prevent="submitComment"
                      >
                        <div
                          class="the_comment-form serv form ignore-select comment-toggle"
                        >
                          <div class="form_for-comment--header d-flex ai-center">
                            <input
                              class="form_for-comment--input flex-grow-1"
                              maxlength="35"
                              name="name"
                              placeholder="Ваше имя"
                              type="text"
                              v-model="commentForm.name"
                              required
                            />
                            <input
                              class="form_for-comment--input flex-grow-1"
                              maxlength="35"
                              name="mail"
                              placeholder="Ваш e-mail (необязательно)"
                              type="text"
                              v-model="commentForm.email"
                            />
                          </div>
                          <div class="form_for-comment--editor p-relative">
                            <div class="bb-editor">
                              <textarea
                                cols="70"
                                name="comments"
                                rows="10"
                                placeholder="Ваш комментарий..."
                                v-model="commentForm.comment"
                                @focus="showCaptchaOnFocus"
                                required
                              ></textarea>
                            </div>
                          </div>
                          <div
                            class="message-info form"
                            :class="{ 'd-none': !showCaptcha }"
                          >
                            <div class="form__row form__row--protect">
                              <label
                                class="form__label form__label--important"
                                for=""
                                >Защита от спама</label
                              >
                              <div
                                class="g-recaptcha"
                                data-language="ru"
                                data-sitekey="6LeMNBgsAAAAAF-cI33csG6ZC9_BKo6x-ljo7yZN"
                                data-theme="light"
                              ></div>
                            </div>
                          </div>
                          <div class="form_for-comment--actions">
                            <button
                              class="form_for-comment--btn"
                              name="submit"
                              type="submit"
                              :disabled="
                                !commentForm.comment ||
                                commentForm.comment.length < 50
                              "
                            >
                              Отправить
                            </button>
                            <button
                              class="form_for-comment--btn cancel-btn"
                              type="button"
                              @click.prevent="cancelReply"
                            >
                              Отмена
                            </button>
                          </div>
                        </div>
                      </form>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Похожие фильмы -->
        <div v-if="relatedMovies.length" class="pagecontinue---related carou">
          <div class="carou__caption">Смотрите также:</div>
          <!--Подборка формируется автоматически на основе жанров и года.-->
          <div class="pagecontinue---content karuselMy-grid">
            <MovieCard
              v-for="(relatedMovie, idx) in relatedMovies"
              :key="relatedMovie.id"
              :movie="relatedMovie"
              :priority="idx === 0"
            />
          </div>
        </div>
      </div>
    </article>

    <div v-else-if="isLoading" class="page-skeleton">Загрузка…</div>

    <div v-else class="no-movie">
      <h1>Фильм не найден</h1>
      <p>Возможно, фильм был удален или перемещен.</p>
      <router-link to="/" class="btn">Вернуться на главную</router-link>
    </div>
  </div>
</template>

<script setup>
import {
  computed,
  ref,
  reactive,
  inject,
  onMounted,
  nextTick,
  watch,
  onBeforeUnmount,
} from "vue";
import MovieCard from "./MovieCard.vue";
import { updateMovieSeo } from "../assets/seoUtils.js";

const props = defineProps({
  category: String,
  id: String,
});

const isDescriptionExpanded = ref(false);
const descrScrollRef = ref(null);
const descrContentRef = ref(null);
const canExpand = ref(false);
const hasMeasured = ref(false);

const normalizedDescription = computed(() =>
  (movie.value?.description || "").replace(/\\n/g, "\n")
);

const stripMdBold = (s) =>
  (s ?? "").replace(/\*\*(.*?)\*\*/g, "$1").replace(/\*\*/g, "");

function updateCanExpand() {
  const content = descrContentRef.value;
  if (!content) {
    canExpand.value = false;
    hasMeasured.value = true;
    return;
  }
  const MAX_COLLAPSED = 160; // как в .js-hide-text
  canExpand.value = content.scrollHeight > MAX_COLLAPSED + 1;
  hasMeasured.value = true;
}

// Добавьте:
let resizeRAF = null;
function scheduleMeasure() {
  if (resizeRAF) cancelAnimationFrame(resizeRAF);
  resizeRAF = requestAnimationFrame(() => {
    updateCanExpand();
    resizeRAF = null;
  });
}

let descrResizeObs = null;

onMounted(() => {
  nextTick(() => {
    updateCanExpand();
    // Точечно следим за реальным контейнером описания
    const el = descrContentRef.value;
    if ("ResizeObserver" in window && el) {
      descrResizeObs = new ResizeObserver(() => scheduleMeasure());
      descrResizeObs.observe(el);
    } else {
      // Фолбэк на редких браузерах
      window.addEventListener("resize", scheduleMeasure, { passive: true });
    }
  });
});

onBeforeUnmount(() => {
  if (descrResizeObs) {
    try {
      descrResizeObs.disconnect();
    } catch {}
    descrResizeObs = null;
  } else {
    window.removeEventListener("resize", scheduleMeasure);
  }
});

const injected =
  typeof window === "undefined" ? inject("moviePayload", null) : null;
const initialPayload =
  typeof window === "undefined"
    ? injected
    : window.__MOVIE_PAYLOAD__ &&
      window.__MOVIE_PAYLOAD__.movie?.id === props.id
    ? window.__MOVIE_PAYLOAD__
    : null;

const state = reactive({
  movie: initialPayload?.movie || null,
  categories: initialPayload?.categories || {},
  related: initialPayload?.related || [],
});

watch(
  () => state.movie && state.movie.description,
  () => nextTick(scheduleMeasure)
);

const isLoading = ref(!state.movie);
async function loadMovie(id = props.id) {
  try {
    isLoading.value = true;
    state.movie = null;
    state.categories = {};
    state.related = [];
    const resp = await fetch(`/api/movie-full/${id}`);
    if (!resp.ok) throw new Error("movie-fetch-failed");
    const data = await resp.json();
    state.movie = data.movie;
    state.categories = data.categories || {};
    state.related = data.related || [];
    if (typeof window !== "undefined") {
      window.__MOVIE_PAYLOAD__ = data;
    }
  } catch (e) {
    console.error("Ошибка загрузки фильма:", e);
  } finally {
    isLoading.value = false;
  }
}
onMounted(() => {
  if (!state.movie || state.movie.id !== props.id) {
    loadMovie();
  } else {
    isLoading.value = false;
  }
});

watch(
  () => props.id,
  (newId) => {
    if (!newId || newId === state.movie?.id) return;
    loadMovie(newId);
  }
);

function formatRating(val) {
  const n = parseFloat(String(val).replace(",", "."));
  if (!isFinite(n)) return String(val ?? "");
  const rounded = Math.round(n * 10) / 10;
  return Math.abs(rounded - Math.round(rounded)) < 1e-9
    ? String(Math.round(rounded))
    : rounded.toFixed(1);
}

// SEO helpers
function upsertTag(selector, create) {
  let el = document.head.querySelector(selector);
  if (!el) {
    el = create();
    document.head.appendChild(el);
  }
  return el;
}
function setMeta(name, content) {
  if (!content) return;
  upsertTag(`meta[name="${name}"]`, () => {
    const m = document.createElement("meta");
    m.setAttribute("name", name);
    return m;
  }).setAttribute("content", content);
}
function setOg(property, content) {
  if (!content) return;
  upsertTag(`meta[property="${property}"]`, () => {
    const m = document.createElement("meta");
    m.setAttribute("property", property);
    return m;
  }).setAttribute("content", content);
}
function setTwitter(name, content) {
  if (!content) return;
  upsertTag(`meta[name="${name}"]`, () => {
    const m = document.createElement("meta");
    m.setAttribute("name", name);
    return m;
  }).setAttribute("content", content);
}
function setCanonical(url) {
  if (!url) return;
  upsertTag('link[rel="canonical"]', () => {
    const l = document.createElement("link");
    l.setAttribute("rel", "canonical");
    return l;
  }).setAttribute("href", url);
}
function setJsonLd(id, obj) {
  const sel = `script[type="application/ld+json"][data-id="${id}"]`;
  let el = document.head.querySelector(sel);
  if (!el) {
    el = document.createElement("script");
    el.type = "application/ld+json";
    el.setAttribute("data-id", id);
    document.head.appendChild(el);
  }
  el.textContent = JSON.stringify(obj);
}

const movie = computed(() => state.movie);

const initialCanExpand = computed(() => {
  const text = movie.value?.description || "";
  if (!text) return false;
  // Достаточно длинный текст или явные блочные/разрывные теги/абзацы
  return (
    text.length > 220 || /\n{2,}/.test(text) || /<p|<br|<li|<div/i.test(text)
  );
});

const kodikDirectUrl = ref("");

watch(
  movie,
  async (m) => {
    kodikDirectUrl.value = "";
    if (!m) return;

    // Если нет KP-ID, но есть флаг iskodik — пробуем достать прямой URL
    if (!m.kinopoiskId && m.iskodik) {
      // 1) если уже пришёл с бэка (вдруг ты добавишь в movies-data.json)
      if (m.kodikPlayer) {
        kodikDirectUrl.value = m.kodikPlayer;
        return;
      }
      if (typeof window === "undefined") return; // важно
      // 2) берём из большого файла через API
      try {
        const r = await fetch(`/api/kodik-url/${m.id}`);
        if (r.ok) {
          const j = await r.json();
          kodikDirectUrl.value = j?.url || "";
        }
      } catch {}
    }
  },
  { immediate: true }
);

const categoryTitle = computed(() => {
  if (!movie.value) return "";
  const map = {
    filmy: "Фильмы",
    films: "Фильмы",
    serialy: "Сериалы",
    serials: "Сериалы",
    anime: "Аниме",
    animes: "Аниме",
    multfilmy: "Мультфильмы",
    multfilm: "Мультфильмы",
    cartoons: "Мультфильмы",
  };
  const slug = movie.value.category;
  return state.categories?.[slug] || map[slug] || "Фильмы и сериалы";
});

const categoryLabel = computed(() => {
  const c = movie.value?.category;
  switch (c) {
    case "filmy":
      return "фильм";
    case "serialy":
    case "serials":
      return "сериал";
    case "anime":
    case "animes":
      return "аниме";
    case "multfilmy":
    case "multfilm":
    case "cartoons":
      return "мультфильм";
    default:
      return "";
  }
});

const isSerialLike = computed(() => {
  const c = movie.value?.category;
  return c === "serialy" || c === "serials" || c === "anime" || c === "animes";
});

const h1Text = computed(() => {
  const m = movie.value;
  if (!m) return "";
  const seasonEpisode = [m.season, m.episode].filter(Boolean).join(" ");
  const year = m.year ? `(${m.year})` : "";
  if (isSerialLike.value) {
    // Для сериалов и аниме: "сериал (2025) смотреть онлайн 1 сезон 1 серия"
    return seasonEpisode
      ? `сериал ${year} смотреть онлайн ${seasonEpisode}`
      : `сериал ${year} смотреть онлайн`;
  }
  // Для фильмов и мультфильмов: "фильм (2025) смотреть онлайн"
  return `фильм ${year} смотреть онлайн`;
});

const h2Text = computed(() => {
  const m = movie.value;
  if (!m) return "";
  const year = m.year ? String(m.year) : "";
  const labelLower = categoryLabel.value || "фильм";
  const isSerial = isSerialLike.value;
  if (isSerial) {
    // "Смотреть онлайн сериал 2025 Название все серии подряд бесплатно в хорошем качестве hd 720 или 1080"
    return `Смотреть онлайн сериал ${year} ${m.title} все серии подряд бесплатно в хорошем качестве hd 720 или 1080`;
  }
  // Для остальных категорий
  return `Смотреть онлайн ${labelLower} ${year} ${m.title} бесплатно в хорошем качестве hd 720 или 1080`;
});

// Функция для правильного формирования пути к изображению
const imageUrl = computed(() => {
  const img = movie.value?.image || "";
  if (!img) return "";
  if (img.startsWith("http")) return img;
  return img.startsWith("/") ? img : `/${img}`;
});
const relPoster = computed(() => {
  const img = movie.value?.image || "";
  if (!img || img.startsWith("http")) return null;
  return img.startsWith("/") ? img : `/${img}`;
});
const posterSrcset = computed(() => {
  const rel = relPoster.value;
  if (!rel) return "";
  const mk = (w) => `/img?src=${encodeURIComponent(rel)}&w=${w}&q=60&f=webp`;
  return [
    `${mk(220)} 220w`,
    `${mk(360)} 360w`,
    `${mk(540)} 540w`,
    `${mk(720)} 720w`,
    `${mk(1080)} 1080w`,
  ].join(", ");
});
const posterSizes = computed(() => isSmallPoster ? "(max-width: 760px) 33vw, (max-width: 1220px) 200px, 200px" : "(max-width: 760px) 42vw, (max-width: 1220px) 240px, 240px");

// Определяем узкие постеры (нативная ширина <= 210px)
const isSmallPoster = ref(false);
function checkPosterSize() {
 if (typeof window === "undefined") return;
 const url = imageUrl.value;
 if (!url) {
   isSmallPoster.value = false;
   return;
 }
 const img = new Image();
 img.onload = () => {
   const w = img.naturalWidth || 0;
   isSmallPoster.value = w > 0 && w <= 210;
 };
 img.onerror = () => (isSmallPoster.value = false);
 img.src = url;
}
watch(imageUrl, () => checkPosterSize(), { immediate: true });

const countriesList = computed(() => {
  const c = movie.value?.country;
  if (!c) return [];
  return String(c)
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
});

const actorsList = computed(() => {
  const a = movie.value?.actors;
  if (!a) return [];
  return String(a)
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
});

const MAX_ACTORS = 15;
const actorsListLimited = computed(() => actorsList.value.slice(0, MAX_ACTORS));

// Настройки отбора и приоритета переводов
const MAX_TRANSLATIONS = 15;

// Явно отсекаем «мусорные» варианты
const RAW_BLACKLIST = new Set(["Реальный перевод", "Субтитры автоперевод"]);

// Чем раньше в списке — тем выше приоритет
const TRANSLATION_PRIORITY = [
  // Типы
  "Дубляж",
  "Дублированный",
  "Профессиональный",
  "Русские субтитры",
  "Субтитры",

  // Популярные студии (пополняйте по вкусу)
  "AniLibria",
  "SHIZA Project",
  "AniDUB",
  "Crunchyroll",
  "Wakanim",
  "AniStar",
  "AnimeVost",
  "Animedia",
  "AniRise",
  "AniBaza",
  "AniJoy",
  "JAM",
  "KOMOREBI",
  "Kitsune Studio",
  "Studio Band",
  "HaronMedia",
  "Freedub Studio",
  "FumoDub",
  "ConeVoice",
  "Inkwell Studio",
  "AniCosmic",
  "AniLeague",
  "AniLiberty",
  "youmiteru",
  "SEKAI PROJECT",
];

// Быстрый поиск веса
const PRIORITY_WEIGHT = (() => {
  const m = new Map();
  let w = 1000;
  for (const name of TRANSLATION_PRIORITY) m.set(name.toLowerCase(), w--);
  return m;
})();

function normalizeTranslationName(s) {
  let name = String(s || "").trim();

  // Убираем тех. суффиксы и скобки
  name = name.replace(/\.?Subtitles$/i, "");
  name = name.replace(/\.?TV$/i, "");
  name = name.replace(/\s*\((?:AniLibria|AniLiberty)[^)]+\)\s*/gi, "");
  name = name.replace(/\s*&\s*Wakanim/i, ""); // оставим Wakanim отдельно

  // Сводим некоторые варианты к каноническому виду
  const low = name.toLowerCase();
  if (low === "anilibria.tv" || low === "anilibria subtitles")
    name = "AniLibria";
  if (low === "aniliberty (anilibria)") name = "AniLibria";
  if (low === "crunchyroll subtitles") name = "Crunchyroll";
  if (low === "anileague.tv") name = "AniLeague";
  if (low === "студия band & wakanim" || low === "studio band & wakanim")
    name = "Wakanim";

  // Приводим к заглавному виду первой буквы (аккуратно)
  return name.trim();
}

function weightTranslation(displayName) {
  const key = displayName.toLowerCase();
  if (PRIORITY_WEIGHT.has(key)) return PRIORITY_WEIGHT.get(key);

  // Общие эвристики
  if (/дубляж|дублирован/i.test(displayName)) return 900;
  if (/субтит/i.test(displayName)) return 700;

  // Слегка поднимаем варианты с «озвучк»
  if (/озвуч/i.test(displayName)) return 650;

  // Дефолт
  return 100;
}

const translationsList = computed(() => {
  const t = movie.value?.translation;
  if (!t) return [];

  // Разворачиваем в массив строк
  const raw = Array.isArray(t)
    ? t.flatMap((s) => String(s).split(","))
    : String(t).split(",");

  // Нормализуем, чистим, убираем дубли
  const seen = new Set();
  const items = [];
  for (const s of raw) {
    const orig = String(s).trim();
    if (!orig || RAW_BLACKLIST.has(orig)) continue;

    const norm = normalizeTranslationName(orig);
    const key = norm.toLowerCase();
    if (!norm || seen.has(key)) continue;

    seen.add(key);
    items.push(norm);
  }

  // Сортируем по весу и алфавиту, обрезаем
  items.sort((a, b) => {
    const wa = weightTranslation(a);
    const wb = weightTranslation(b);
    if (wb !== wa) return wb - wa;
    return a.localeCompare(b, "ru");
  });

  return items.slice(0, MAX_TRANSLATIONS);
});

// заменить тело updateSeo
function updateSeo() {
  if (typeof window === "undefined") return;
  updateMovieSeo(movie.value, categoryTitle.value);
}

onMounted(() => updateSeo());
watch(movie, () => updateSeo());
watch(imageUrl, () => updateSeo());

const players = computed(() => {
  const m = movie.value;
  if (!m) return [];

  const hasKp = !!m.kinopoiskId;
  if (hasKp) {
    // исходный список
    let list = [
      { type: "sv", kinopoiskId: m.kinopoiskId },
      {
        type: "iframe",
        src: `https://polygamist-as.stloadi.live/?kp=${m.kinopoiskId}&token=eb79c8a500d725f071c3bcc1e975bb`,
      },
      {
        type: "iframe",
        src: `https://api.atomics.ws/embed/kp/${m.kinopoiskId}?theme=2&theme=2`,
      },
      { type: "kodik", kinopoiskId: m.kinopoiskId },
    ];

    // запрет стран оставляем как было
    const restrictedCountries = [
      /*...*/
    ];
    const movieCountries = m.country
      ? m.country.split(",").map((c) => c.trim())
      : [];
    const isRestricted = movieCountries.some((mc) =>
      restrictedCountries.includes(mc)
    );
    if (isRestricted) list = list.filter((p) => p.type !== "kodik");

    // если iskodik — можно поднимать kodik (как было)
    if (!isRestricted && m.iskodik) {
      const i = list.findIndex((p) => p.type === "kodik");
      if (i > -1) {
        const [kd] = list.splice(i, 1);
        list.unshift(kd);
      }
    }

    // ВАЖНО: поднимем iframe над SV (SV вторая позиция)
    const iIframe = list.findIndex((p) => p.type === "iframe");
    const iSv = list.findIndex((p) => p.type === "sv");
    if (iIframe > -1 && iSv > -1 && iIframe > iSv) {
      const [ifr] = list.splice(iIframe, 1);
      list.splice(iSv, 0, ifr); // iframe перед SV
    }

    list = list.map((p, i) => ({ ...p, name: `Плеер ${i + 1}` }));
    if (m.youtubeId) {
      list.push({
        name: "Трейлер",
        type: "youtube",
        src: `https://www.youtube.com/embed/${m.youtubeId}`,
      });
    }
    return list;
  }

  // без KP
  const mains = [];
  if (m.iskodik) {
    const url = m.kodikPlayer || kodikDirectUrl.value || "";
    if (url) mains.push({ type: "iframe", src: url });
  }
  let list = mains.map((p, i) => ({ ...p, name: `Плеер ${i + 1}` }));
  if (m.youtubeId)
    list.push({
      name: "Трейлер",
      type: "youtube",
      src: `https://www.youtube.com/embed/${m.youtubeId}`,
    });
  return list;
});

async function precheckIframePlayers() {
  const list = players.value;
  const checks = list.map(async (p, i) => {
    if (p.type !== "iframe") return;
    try {
      const res = await probePlayer(p.src);
      if (!res) return;
      if (isAlloha(p.src)) {
        if (res.matched === true) markPlayerFailed(i);
      } else {
        if (!res.ok) markPlayerFailed(i);
      }
    } catch {}
  });
  await Promise.all(checks);
  // if (failedPlayers.value[activeTab.value]) switchToNextPlayer(activeTab.value);
}

const activeTab = ref(0);
const isLightOff = ref(false);

const failedPlayers = ref([]);
const playerReady = ref({});

watch(
  players,
  (list) => {
    failedPlayers.value = Array(list.length).fill(false);
    const prev = playerReady.value || {};
    const next = {};
    list.forEach((_, idx) => {
      next[idx] = Boolean(prev[idx]);
    });
    playerReady.value = next;
  },
  { immediate: true }
);

watch(activeTab, (i) => {
  const p = players.value?.[i];
  if (p?.type === "sv") ensureCdnVideoHub();
  if (p?.type === "iframe") preconnectForPlayers([p]);
});

const hasWorkingPlayer = computed(() => {
  const list = players.value || [];
  if (list.length === 0) return false;
  // Никогда не скрываем контейнер, если первый плеер есть (даже если он упал)
  if (list.length > 0) return true;
  return list.some((_, i) => !failedPlayers.value[i]);
});

function markPlayerReady(index) {
  if (playerReady.value[index]) return;
  playerReady.value = { ...playerReady.value, [index]: true };
}

function markPlayerFailed(index) {
  const total = players.value.length;
  if (!total) return;

  const snapshot = failedPlayers.value.slice(0, total);
  while (snapshot.length < total) snapshot.push(false);

  if (!snapshot[index]) {
    snapshot[index] = true;
  }

  failedPlayers.value = snapshot;
  markPlayerReady(index);
}

// // Заменить существующую версию на эту (пропускает упавшие)
// function switchToNextPlayer(fromIndex) {
//   for (let i = fromIndex + 1; i < players.value.length; i++) {
//     if (!failedPlayers.value[i]) {
//       activeTab.value = i;
//       return true;
//     }
//   }
//   for (let i = 0; i < fromIndex; i++) {
//     if (!failedPlayers.value[i]) {
//       activeTab.value = i;
//       return true;
//     }
//   }
//   return false;
// }

function failAndSwitch(index) {
  markPlayerFailed(index);
}

function safeFail(index) {
  if (index === activeTab.value) failAndSwitch(index);
  else markPlayerFailed(index);
}

function isAlloha(url) {
  try {
    return /stloadi\.live/i.test(new URL(url).hostname);
  } catch {
    return false;
  }
}

const DBG = true;
function dbg(...a) {
  if (DBG) console.log("[PlayerDBG]", ...a);
}

const allohaReadyByIndex = ref({});
function markAllohaReady(index) {
  allohaReadyByIndex.value[index] = true;
  markPlayerReady(index);
  // clearFallbackTimer();
}

const svReadyByIndex = ref({});
function markSvReady(index) {
  svReadyByIndex.value[index] = true;
  markPlayerReady(index);
  // clearFallbackTimer();
}

function markSvError(index) {
  markPlayerFailed(index);
}

function handleWindowMessage(e) {
  try {
    const host = new URL(e.origin).hostname;
    if (/stloadi\.live/i.test(host)) {
      const idx = activeTab.value;
      const p = players.value[idx];
      // Сбрасываем таймер только если текущая вкладка — Alloha iframe
      if (p && p.type === "iframe" && isAlloha(p.src)) {
        markAllohaReady(idx);
      }
    }
  } catch {}
}

function handleCdnMessage(e) {
  try {
    const host = new URL(e.origin).hostname;
    if (/player\.cdnvideohub\.com/i.test(host)) {
      const idx = activeTab.value;
      const p = players.value[idx];
      if (!p || p.type !== "sv") return;

      const d = e.data;
      const text = typeof d === "string" ? d : JSON.stringify(d || "");
      const isError =
        /error|not[_-\s]?found|no[_-\s]?content|unavailable|fail/i.test(text);
      const isReady = /ready|loaded|init|player[_-\s]?ready/i.test(text);

      dbg("SV MSG", {
        origin: e.origin,
        isError,
        isReady,
        elapsed: svWaitStart.value
          ? Math.round(performance.now() - svWaitStart.value)
          : null,
        sample: text.slice(0, 120),
      });

      if (isError) {
        markSvError(idx);
        return;
      }
      if (isReady) {
        markSvReady(idx);
        return;
      }

      // неявное "живой" — не скрываем, чтобы не рубить рабочие кейсы
      markSvReady(idx);
    }
  } catch {}
}

onBeforeUnmount(() => {
  window.removeEventListener("message", handleWindowMessage);
  window.removeEventListener("message", handleCdnMessage);
  // clearFallbackTimer();
});

// Refs and helpers for auto-switching between players
// let fallbackTimer = null;
let svMessageTimer = null; // +++ новый таймер ожидания ready-сообщения
const iframeRefs = ref({});
const svWaitStart = ref(0);

function registerIframeRef(index, el) {
  if (!el) {
    delete iframeRefs.value[index];
    return;
  }
  iframeRefs.value[index] = el;
}

// function clearFallbackTimer() {
//   if (fallbackTimer) {
//     clearTimeout(fallbackTimer);
//     fallbackTimer = null;
//   }
//   if (svMessageTimer) {
//     // +++ чистим второй таймер
//     clearTimeout(svMessageTimer);
//     svMessageTimer = null;
//   }
// }
function clearFallbackTimer() {}
function svHasMainIframe(index) {
  const container = document.getElementById(`player_video_${index}`);
  if (!container) return false;

  const vp = container.querySelector("video-player");
  const scope = vp && vp.shadowRoot ? vp.shadowRoot : container;

  // Основной iframe плеера
  const main = scope.querySelector(
    'iframe.vk-player-iframe, iframe[src*="vk.com"], iframe[src*="cdnvideohub"], iframe[src*="vkvideo"]'
  );
  if (main) return true;

  // Есть iframe, но он служебный (pixel/ad) → не считаем загрузкой
  // Если здесь найдутся только такие — возвращаем false
  return false;
}

function waitForSvMainIframe(index, maxWait = 6000) {
  return new Promise((resolve) => {
    const started = Date.now();
    const done = (ok) => {
      try {
        observer && observer.disconnect();
      } catch {}
      resolve(ok);
    };

    const tick = () => {
      if (svHasMainIframe(index)) return done(true);
      if (Date.now() - started >= maxWait) return done(false);
      setTimeout(tick, 300);
    };

    const container = document.getElementById(`player_video_${index}`);
    if (!container) return done(false);

    const vp = container.querySelector("video-player");
    const scope = vp && vp.shadowRoot ? vp.shadowRoot : container;

    let observer = null;
    try {
      observer = new MutationObserver(() => {
        if (svHasMainIframe(index)) done(true);
      });
      observer.observe(scope, { childList: true, subtree: true });
    } catch {}

    tick();
  });
}

async function probePlayer(url) {
  try {
    const r = await fetch("/api/probe-player?url=" + encodeURIComponent(url));
    const j = await r.json();
    dbg("probe", { url, j });
    // j = { ok: boolean, status: number, matched: boolean }
    return j;
  } catch {
    // treat as unknown on network error
    return { ok: null, status: 0, matched: false };
  }
}

async function handleIframeLoad(index) {
  if (activeTab.value !== index) return;
  const p = players.value[index];
  if (!p || p.type !== "iframe") return;

  const runProbe = async () => {
    if (activeTab.value !== index) return;
    let res = null;

    try {
      res = await probePlayer(p.src);
    } catch {}

    if (activeTab.value !== index) return;

    // if (res && res.matched === true) {
    //   markPlayerReady(index);
    //   failAndSwitch(index);
    //   return;
    // }

    if (res && (res.ok === true || res.ok === null)) {
      // clearFallbackTimer();
      markPlayerReady(index);
      return;
    }

    markPlayerFailed(index);
  };

  if (isAlloha(p.src)) {
    runProbe();
    return;
  }

  const idle = window.requestIdleCallback || ((cb) => setTimeout(cb, 500));
  idle(runProbe);
}

function handleYoutubeLoad(index) {
  markPlayerReady(index);
}

// function scheduleAutoFallback(index) {
//   clearFallbackTimer();
//   const p = players.value[index];
//   if (!p) return;

//   dbg("schedule", {
//     index,
//     type: p.type,
//     url: p.src,
//     isAlloha: isAlloha(p.src),
//   });

//   if (p.type === "sv") {
//     const startWait = () => {
//       svWaitStart.value = performance.now();
//       // 1) ждем появления главного iframe
//       waitForSvMainIframe(index, 4000).then((found) => {
//         dbg("SV MAIN IFRAME", {
//           found,
//           elapsed: Math.round(performance.now() - svWaitStart.value),
//         });

//         if (
//           !found &&
//           !svReadyByIndex.value[index] &&
//           !failedPlayers.value[index]
//         ) {
//           // нет iframe — фейлим
//           safeFail(index);
//           return;
//         }

//         // 2) iframe есть, ждем ready-сообщение еще 4.5s
//         if (!svReadyByIndex.value[index]) {
//           svMessageTimer = setTimeout(() => {
//             if (!svReadyByIndex.value[index] && !failedPlayers.value[index]) {
//               safeFail(index);
//             }
//           }, 4500);
//         }
//       });
//     };

//     if (cdnPlayerLoaded.value) startWait();
//     else {
//       const stop = watch(cdnPlayerLoaded, (loaded) => {
//         if (!loaded) return;
//         stop();
//         startWait();
//       });
//     }
//     return;
//   } else if (p.type === "kodik") {
//     fallbackTimer = setTimeout(() => {
//       if (activeTab.value !== index) return;
//       const container = document.getElementById("kodik-player");
//       const iframe = container ? container.querySelector("iframe") : null;
//       if (!iframe) safeFail(index);
//     }, 12000);
//   }
// }

function handleIframeError(index) {
  if (activeTab.value !== index) return;
  const p = players.value[index];

  if (p && p.type === "iframe" && isAlloha(p.src)) {
    probePlayer(p.src)
      .then((res) => {
        if (activeTab.value !== index) return;

        if (res && res.matched === true) {
          markPlayerReady(index);
          // Было: failAndSwitch(index);
          markPlayerFailed(index);
        } else {
          markPlayerReady(index);
          // clearFallbackTimer();
        }
      })
      .catch(() => {
        markPlayerFailed(index);
      });
    return;
  }

  // markPlayerReady(index);
  // failAndSwitch(index);
}

function whenLCP(cb) {
  try {
    let fired = false;
    const done = () => {
      if (!fired) {
        fired = true;
        cb();
      }
    };
    const po = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      if (entries && entries.length) {
        try {
          po.disconnect();
        } catch {}
        done();
      }
    });
    po.observe({ type: "largest-contentful-paint", buffered: true });
    setTimeout(done, 1500); // фолбэк, если LCP не пойман
  } catch {
    setTimeout(cb, 1500);
  }
}

// ...existing imports and code above...

onMounted(() => {
  // НЕ запускаем precheck сразу; дождёмся idle/взаимодействия:
  const idle = window.requestIdleCallback || ((cb) => setTimeout(cb, 1200));
  idle(() => {
    // Опционально: ничего не делаем, пока пользователь не коснется контролов плеера
    // precheckIframePlayers(); // ← убрано
    const kdx = getKodikIndex();
    if (kdx >= 0) initKodik(kdx);
  });

  whenLCP(() => {
    // после LCP можно прогреть/подгрузить активный плеер, без клика
    const i = activeTab.value;
    const p = players.value?.[i];
    if (p?.type === "sv") {
      ensureCdnVideoHub(); // загрузит runtime, UI инжектнется по IO (как сейчас)
    }
    // если первым идёт iframe — он и так создаётся по шаблону/IO, LCP не трогаем
  });

  // previously: immediate watch(activeTab) touching document
  watch(
    activeTab,
    (newIndex) => {
      const player = players.value[newIndex];
      if (!player) return;

      nextTick(() => {
        if (typeof document === "undefined") return;

        if (player.type === "sv") {
          const containerId = `player_video_${newIndex}`;
          const container = document.getElementById(containerId);
          if (!container) return;

          // гарантируем загрузку runtime (UMD)
          ensureCdnVideoHub();

          const hasMain = svHasMainIframe(newIndex);
          const hasUiScript = !!container.querySelector(
            "script[data-cdnvh-ui]"
          );
          if (!hasMain) {
            const injectUI = () => {
              if (svHasMainIframe(newIndex)) return;
              const stale = container.querySelector("script[data-cdnvh-ui]");
              if (stale && stale.parentNode)
                stale.parentNode.removeChild(stale);
              const s = document.createElement("script");
              s.src = "/api/cdnvh-playerui.js";
              s.async = true;
              s.setAttribute("data-cdnvh-ui", "1");
              container.appendChild(s);
            };

            const startWhenVisible = () => {
              if ("IntersectionObserver" in window) {
                let fired = false;
                const io = new IntersectionObserver(
                  (entries) => {
                    if (fired) return;
                    if (entries.some((e) => e.isIntersecting)) {
                      fired = true;
                      io.disconnect();
                      injectUI();
                    }
                  },
                  { rootMargin: "200px 0px" }
                );
                io.observe(container);
                setTimeout(() => {
                  if (!fired) {
                    fired = true;
                    io.disconnect();
                    injectUI();
                  }
                }, 800);
              } else {
                injectUI();
              }
            };

            if (cdnPlayerLoaded.value) startWhenVisible();
            else {
              const stop = watch(cdnPlayerLoaded, (loaded) => {
                if (!loaded) return;
                stop();
                startWhenVisible();
              });
            }
          }
        }
        // else if (player.type === "kodik") {
        //   initKodik(newIndex);
        // }
        // scheduleAutoFallback(newIndex);
      });
    },
    { immediate: true, deep: true }
  );
});

// Safer: guard document usage for this watcher too
watch(isLightOff, (newValue) => {
  if (typeof document === "undefined") return;
  const playerContainer = document.getElementById("player-container");
  if (newValue) {
    document.body.classList.add("light-off");
    if (playerContainer) {
      playerContainer.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  } else {
    document.body.classList.remove("light-off");
  }
});

// ...rest of file...

// Похожие фильмы (той же категории и жанра)
const relatedMovies = computed(() => state.related || []);

async function refreshRelatedIfNeeded() {
  if (typeof window === "undefined") return; // SSR guard
  if (!movie.value || state.related?.length) return;
  try {
    const resp = await fetch(`/api/related/${movie.value.id}`);
    if (resp.ok) {
      const data = await resp.json();
      state.related = data.items || [];
    }
  } catch (e) {
    console.error("Ошибка загрузки похожих:", e);
  }
}

// вместо immediate SSR-вызова — запуск на клиенте
onMounted(() => {
  refreshRelatedIfNeeded();
});

onMounted(() => {
  preconnectForPlayers(players.value);
});

watch(
  players,
  (list) => {
    preconnectForPlayers(list);
    const idx = activeTab.value || 0;
    if (list[idx]?.type === "kodik") nextTick(() => initKodik(idx));
  },
  { deep: true /* immediate: false по умолчанию */ }
);

// Состояние для оценок страницы
const pageLikes = ref(0);
const pageDislikes = ref(0);
const userVote = ref(null);
const isVotingPage = ref(false);
const ratingsReady = ref(false);
let initialRatingsLoad = null;

const calculatedRating = computed(() => {
  const likes = pageLikes.value;
  const dislikes = pageDislikes.value;
  const totalVotes = likes + dislikes;

  if (totalVotes === 0) {
    return "0";
  }

  const rating = (likes / totalVotes) * 10;
  return Math.round(rating);
});

// Состояние для комментариев
const comments = ref([]);
const commentsCount = ref(0);
const replyToCommentId = ref(null); // ID комментария, на который отвечаем
const commentForm = ref({
  name: "",
  email: "",
  comment: "",
});
const showCaptcha = ref(false);

// Обработка комментариев для вложенности
const processedComments = computed(() => {
  const commentMap = {};
  comments.value.forEach((comment) => {
    commentMap[comment.id] = { ...comment, children: [] };
  });

  const result = [];
  comments.value.forEach((comment) => {
    if (comment.parentId && commentMap[comment.parentId]) {
      commentMap[comment.parentId].children.push(commentMap[comment.id]);
    } else {
      result.push(commentMap[comment.id]);
    }
  });

  const flatten = (comments, level = 0) => {
    let flatList = [];
    comments.forEach((comment) => {
      flatList.push({ ...comment, level });
      if (comment.children.length) {
        flatList = flatList.concat(flatten(comment.children, level + 1));
      }
    });
    return flatList;
  };

  return flatten(result);
});

// Загрузка оценок страницы (сервер → fallback localStorage)
const loadPageRatings = async () => {
  // 1) Мгновенно применяем локальное состояние (убирает окно гонки)
  try {
    const savedVote = localStorage.getItem(`page_vote_${props.id}`);
    if (savedVote) userVote.value = savedVote;
    const savedRatings = localStorage.getItem(`page_ratings_${props.id}`);
    if (savedRatings) {
      const { likes, dislikes } = JSON.parse(savedRatings);
      pageLikes.value = likes;
      pageDislikes.value = dislikes;
      ratingsReady.value = true; // можно голосовать сразу
    }
  } catch {}

  // 2) Затем подтягиваем канонические значения с сервера
  try {
    const resp = await fetch(`/api/movie-ratings/${props.id}`, {
      cache: "no-store",
    });
    if (resp.ok) {
      const { pageLikes: likes = 0, pageDislikes: dislikes = 0 } =
        await resp.json();
      pageLikes.value = likes;
      pageDislikes.value = dislikes;
      localStorage.setItem(
        `page_ratings_${props.id}`,
        JSON.stringify({ likes, dislikes })
      );
    } else if (!ratingsReady.value) {
      const { likes, dislikes } = calculateInitialRatings(movie.value);
      pageLikes.value = likes;
      pageDislikes.value = dislikes;
    }
  } catch (error) {
    console.error("Ошибка загрузки оценок:", error);
    if (!ratingsReady.value) {
      const { likes, dislikes } = calculateInitialRatings(movie.value);
      pageLikes.value = likes;
      pageDislikes.value = dislikes;
    }
  } finally {
    ratingsReady.value = true;
  }
};

// Функция для расчета начальных оценок на основе рейтинга фильма
const calculateInitialRatings = (movie) => {
  let rating = 0;

  // Используем KP рейтинг если есть, иначе IMDB
  if (movie.kpRating) {
    rating = parseFloat(movie.kpRating);
  } else if (movie.imdbRating) {
    rating = parseFloat(movie.imdbRating);
  } else {
    // Если рейтинга нет, используем средние значения
    rating = 7.0;
  }

  // Рассчитываем лайки и дизлайки на основе рейтинга
  // Рейтинг 10 = 100 лайков, 0 дизлайков
  // Рейтинг 5 = 50 лайков, 50 дизлайков
  // Рейтинг 0 = 0 лайков, 100 дизлайков
  const likes = Math.round(rating * 10);
  const dislikes = Math.round((10 - rating) * 10);

  return { likes, dislikes };
};

// Голосование за страницу (серверная запись)
const votePage = async (voteType) => {
  if (isVotingPage.value || !ratingsReady.value) return; // ждём первичную инициализацию
  const previousVote = userVote.value;
  const newVote = previousVote === voteType ? null : voteType;

  isVotingPage.value = true;
  try {
    const resp = await fetch("/api/vote-page", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      keepalive: true,
      body: JSON.stringify({
        movieId: props.id,
        voteType: newVote,
        previousVote,
      }),
    });
    if (!resp.ok) throw new Error("vote API failed");
    const data = await resp.json();
    pageLikes.value = data.pageLikes;
    pageDislikes.value = data.pageDislikes;
    userVote.value = newVote;

    if (newVote) localStorage.setItem(`page_vote_${props.id}`, newVote);
    else localStorage.removeItem(`page_vote_${props.id}`);
    localStorage.setItem(
      `page_ratings_${props.id}`,
      JSON.stringify({
        likes: pageLikes.value,
        dislikes: pageDislikes.value,
      })
    );

    window.dispatchEvent(
      new CustomEvent("ratings-updated", {
        detail: {
          movieId: props.id,
          likes: pageLikes.value,
          dislikes: pageDislikes.value,
        },
      })
    );
  } catch (error) {
    console.error("Ошибка голосования:", error);
  } finally {
    isVotingPage.value = false;
  }
};

// Загрузка комментариев
const loadComments = async () => {
  try {
    // Загружаем комментарии с сервера
    const response = await fetch(`/api/movie-comments/${props.id}`);

    if (response.ok) {
      const result = await response.json();
      comments.value = result.comments || [];
      commentsCount.value = comments.value.length;
    } else {
      console.error("Ошибка загрузки комментариев с сервера");
      // Fallback к локальным данным
      if (movie.value && movie.value.comments) {
        comments.value = movie.value.comments;
        commentsCount.value = movie.value.comments.length;
      } else {
        comments.value = [];
        commentsCount.value = 0;
      }
    }
  } catch (error) {
    console.error("Ошибка загрузки комментариев:", error);
    // Fallback к локальным данным
    if (movie.value && movie.value.comments) {
      comments.value = movie.value.comments;
      commentsCount.value = movie.value.comments.length;
    } else {
      comments.value = [];
      commentsCount.value = 0;
    }
  }
};

// Отправка комментария
const submitComment = async () => {
  try {
    if (!commentForm.value.comment || commentForm.value.comment.length < 50) {
      alert("Комментарий должен содержать минимум 50 знаков");
      return;
    }

    // Проверяем reCAPTCHA
    let token = null;
    if (window.grecaptcha) {
      token = window.grecaptcha.getResponse();
      if (!token) {
        alert("Пожалуйста, подтвердите, что вы не робот.");
        return;
      }
    }

    // Создаем тело запроса
    const requestBody = {
      movieId: props.id,
      name: commentForm.value.name || "Гость",
      email: commentForm.value.email,
      comment: commentForm.value.comment,
      "g-recaptcha-response": token,
      parentId: replyToCommentId.value,
    };

    // Сохраняем комментарий через API
    const response = await fetch("/api/add-comment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error("Ошибка сервера при сохранении комментария");
    }

    const result = await response.json();
    console.log("Комментарий успешно сохранен:", result);

    // Очищаем форму и состояние
    commentForm.value.comment = "";
    commentForm.value.name = ""; // Опционально, можно сохранять
    commentForm.value.email = ""; // Опционально, можно сохранять
    showCaptcha.value = false;
    replyToCommentId.value = null;

    // Сбрасываем reCAPTCHA
    if (window.grecaptcha) {
      window.grecaptcha.reset();
    }

    // Перезагружаем комментарии
    await loadComments();
  } catch (error) {
    console.error("Ошибка отправки комментария:", error);
    alert("Ошибка при отправке комментария. " + error.message);
  }
};

// Установить комментарий для ответа
const replyTo = (commentId) => {
  replyToCommentId.value = commentId;
};

// Отменить ответ
const cancelReply = () => {
  replyToCommentId.value = null;
};

const isVotingComment = ref({});
const setVotingComment = (id, val) => {
  isVotingComment.value = { ...isVotingComment.value, [id]: !!val };
};
const isCommentLocked = (id) => !!isVotingComment.value[id];

// Голосование за комментарий
const voteComment = async (commentId, voteType) => {
  try {
    const comment = comments.value.find((c) => c.id === commentId);
    if (!comment) return;
    if (isCommentLocked(commentId)) return;

    // Создаем уникальный ключ для localStorage
    const voteKey = `comment_vote_${props.id}_${commentId}`;

    // Загружаем предыдущий голос пользователя из localStorage
    const previousVote = localStorage.getItem(voteKey);
    const newVote = previousVote === voteType ? null : voteType;

    // Обновляем рейтинг
    if (previousVote === "like") comment.rating--;
    if (previousVote === "dislike") comment.rating++;

    if (newVote === "like") comment.rating++;
    if (newVote === "dislike") comment.rating--;

    // Сохраняем новый голос пользователя в localStorage
    if (newVote) {
      localStorage.setItem(voteKey, newVote);
    } else {
      localStorage.removeItem(voteKey);
    }

    // Сохраняем голос через API
    try {
      setVotingComment(commentId, true);
      const response = await fetch("/api/vote-comment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        keepalive: true,
        cache: "no-store",
        body: JSON.stringify({
          movieId: props.id,
          commentId: commentId,
          voteType: newVote,
          previousVote: previousVote,
        }),
      });

      if (!response.ok) {
        throw new Error("Ошибка сервера при сохранении голоса");
      }

      const result = await response.json();
      // Обновляем рейтинг комментария с серверными данными
      comment.rating = result.comment.rating;
    } catch (apiError) {
      console.error("Ошибка API при сохранении голоса:", apiError);
      // Откатываем изменения при ошибке
      if (previousVote === "like") comment.rating--;
      if (previousVote === "dislike") comment.rating++;

      if (voteType === "like") comment.rating++;
      if (voteType === "dislike") comment.rating--;

      comment.userVote = previousVote;
      alert("Ошибка при сохранении голоса. Попробуйте еще раз.");
    } finally {
      setVotingComment(commentId, false);
    }
  } catch (error) {
    console.error("Ошибка голосования за комментарий:", error);
  }
};

// Показываем капчу при фокусе на поле комментария
const showCaptchaOnFocus = async () => {
  showCaptcha.value = true;

  // Ждем обновления DOM
  await nextTick();

  // Проверяем, есть ли уже reCAPTCHA
  const recaptchaContainer = document.querySelector(".g-recaptcha");

  if (recaptchaContainer && window.grecaptcha) {
    // Если reCAPTCHA уже существует, сбрасываем её
    try {
      window.grecaptcha.reset();
    } catch (error) {
      console.log("reCAPTCHA reset error:", error);
      // Если не удалось сбросить, пересоздаем
      await recreateRecaptcha();
    }
  } else if (window.grecaptcha) {
    // Если reCAPTCHA не существует, создаем заново
    await recreateRecaptcha();
  } else {
    // Если grecaptcha не загружен, ждем загрузки
    console.log("reCAPTCHA не загружен, ждем...");
    await waitForRecaptcha();
    await recreateRecaptcha();
  }
};

// Функция для пересоздания reCAPTCHA
const recreateRecaptcha = async () => {
  try {
    // Очищаем старый контейнер
    const oldContainer = document.querySelector(".g-recaptcha");
    if (oldContainer) {
      oldContainer.remove();
    }

    // Создаем новый div для reCAPTCHA
    const recaptchaDiv = document.createElement("div");
    recaptchaDiv.className = "g-recaptcha";
    recaptchaDiv.setAttribute(
      "data-sitekey",
      "6LeMNBgsAAAAAF-cI33csG6ZC9_BKo6x-ljo7yZN"
    );
    recaptchaDiv.setAttribute("data-theme", "light");
    recaptchaDiv.setAttribute("data-language", "ru");

    // Находим контейнер для reCAPTCHA и вставляем новый div
    const recaptchaContainer = document.querySelector(".form__row--protect");
    if (recaptchaContainer) {
      recaptchaContainer.appendChild(recaptchaDiv);

      // Рендерим reCAPTCHA
      window.grecaptcha.render(recaptchaDiv, {
        sitekey: "6LeMNBgsAAAAAF-cI33csG6ZC9_BKo6x-ljo7yZN",
        theme: "light",
        language: "ru",
      });
    }
  } catch (error) {
    console.error("Ошибка инициализации reCAPTCHA:", error);
  }
};

// Функция для получения голоса пользователя за комментарий
const getUserVote = (commentId) => {
  const voteKey = `comment_vote_${props.id}_${commentId}`;
  return localStorage.getItem(voteKey);
};

const waitForRecaptcha = () => {
  return new Promise((resolve) => {
    if (window.grecaptcha) return resolve();
    const s = document.createElement("script");
    s.src = "https://www.google.com/recaptcha/api.js?hl=ru";
    s.async = true;
    s.defer = true;
    s.onload = () => resolve();
    s.onerror = () => resolve();
    document.head.appendChild(s);
  });
};

// Инициализация при монтировании
onMounted(() => {
  window.addEventListener("message", handleWindowMessage);
  window.addEventListener("message", handleCdnMessage);

  const defer = (fn) =>
    "requestIdleCallback" in window
      ? requestIdleCallback(fn, { timeout: 3000 })
      : setTimeout(fn, 1500);

  defer(() => {
    initialRatingsLoad = loadPageRatings();
  });
  defer(() => {
    loadComments();
  });

  const kdx = getKodikIndex();
  if (kdx >= 0) initKodik(kdx);
});

const isVotingDisabled = computed(
  () => isVotingPage.value || !ratingsReady.value
);

const cdnPlayerLoaded = ref(false);
let cdnLoadPromise = null;

// безопасно для SSR
function ensurePreconnect(origin) {
  if (typeof document === "undefined") return;
  if (!origin) return;
  const href = origin.replace(/\/+$/, "");
  if (document.querySelector(`link[rel="preconnect"][href="${href}"]`)) return;
  const l = document.createElement("link");
  l.rel = "preconnect";
  l.href = href;
  l.crossOrigin = "";
  document.head.appendChild(l);
}

function preconnectForPlayers(list = []) {
  if (typeof document === "undefined") return;
  const origins = Array.from(
    new Set(
      (list || [])
        .filter((p) => p && p.type === "iframe" && p.src)
        .map((p) => {
          try {
            return new URL(p.src).origin;
          } catch {
            return null;
          }
        })
        .filter(Boolean)
    )
  );
  origins.forEach(ensurePreconnect);
}

// и здесь тоже защита на SSR
function ensureCdnVideoHub() {
  if (typeof document === "undefined") return;
  if (cdnPlayerLoaded.value) return;

  const addPre = (href) => {
    if (!document.querySelector(`link[rel="preconnect"][href="${href}"]`)) {
      const l = document.createElement("link");
      l.rel = "preconnect";
      l.href = href;
      l.crossOrigin = "anonymous";
      document.head.appendChild(l);
    }
  };
  addPre("https://player.cdnvideohub.com");
  addPre("https://plapi.cdnvideohub.com");

  if (document.querySelector('script[src*="/api/cdnvh-umd.js"]')) {
    cdnPlayerLoaded.value = true;
    return;
  }

  const s = document.createElement("script");
  s.src = "/api/cdnvh-umd.js";
  s.async = true;
  s.onload = () => {
    cdnPlayerLoaded.value = true;
  };
  document.head.appendChild(s);
}

watch(
  players,
  (list) => {
    if (typeof document === "undefined") return; // SSR guard
    const idx = activeTab.value || 0;
    const p = list[idx];
    if (!p) return;
    if (p.type === "kodik") {
      nextTick(() => initKodik(idx));
    }
  },
  { immediate: true, deep: true }
);

watch(
  () => state.movie && state.movie.id,
  () => {
    activeTab.value = 0;
    isDescriptionExpanded.value = false;
    hasMeasured.value = false;
    playerReady.value = {};
  }
);

function probeKodikOnInject(index, opts = {}) {
  const container = document.getElementById("kodik-player");
  if (!container) return;

  let stopped = false;
  const stop = () => {
    stopped = true;
    try {
      obs && obs.disconnect();
    } catch {}
    if (noIframeTimer) {
      clearTimeout(noIframeTimer);
      noIframeTimer = null;
    }
    if (hardStop) {
      clearTimeout(hardStop);
    }
  };

  // быстрый таймер: только после onload лоадера
  let noIframeTimer = null;
  if (opts.startQuick) {
    noIframeTimer = setTimeout(() => {
      if (stopped) return;
      const iframe = container.querySelector("iframe");
      if (!iframe) safeFail(index); // нет iframe — считаем нерабочим
      stop();
    }, 3600); // можно 3.0–4.0s
  }

  // как только появился iframe — считаем ОК (без серверной проверки)
  const tryMarkReady = () => {
    if (stopped) return;
    const iframe = container.querySelector("iframe");
    if (!iframe) return;
    if (noIframeTimer) {
      clearTimeout(noIframeTimer);
      noIframeTimer = null;
    }
    // clearFallbackTimer();
    markPlayerReady(index);
    stop();
  };

  const obs = new MutationObserver(() => {
    tryMarkReady();
  });
  obs.observe(container, { childList: true, subtree: true });

  // страховка от зависания
  const hardStop = setTimeout(stop, 10000);
}

function initKodik(index) {
  if (typeof document === "undefined") return;
  const container = document.getElementById("kodik-player");
  if (!container) return;

  container.innerHTML = "";
  const oldLoader = document.querySelector("script[data-kodik-loader]");
  if (oldLoader && oldLoader.parentNode)
    oldLoader.parentNode.removeChild(oldLoader);

  window.kodikAddPlayers = {
    kinopoiskID: String(players.value[index].kinopoiskId),
  };

  const tryLoad = (src) =>
    new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = src;
      s.async = true;
      s.setAttribute("data-kodik-loader", "1");
      s.onload = () => resolve(true);
      s.onerror = () => reject(new Error("load-failed"));
      document.head.appendChild(s);
    });

  (async () => {
    try {
      // 1) прямой загрузчик
      await tryLoad("https://kodik-add.com/add-players.min.js");
      probeKodikOnInject(index, { startQuick: true });
    } catch {
      try {
        // 2) фолбэк через наш сервер — обходит блокировки/AdBlock
        await tryLoad("/api/kd-loader.js");
        probeKodikOnInject(index, { startQuick: true });
      } catch {
        // 3) оба не загрузились → считаем плеер недоступным
        safeFail(index);
      }
    }
  })();
}

function getKodikIndex() {
  return players.value.findIndex((p) => p.type === "kodik");
}

// Описание: разбиваем по пустым строкам, если нет HTML-версии
const descriptionParagraphs = computed(() => {
  if (!movie.value) return [];
  if (movie.value.descriptionHtml) return [];
  const text = movie.value.description || "";
  // Разделяем по двойным переводам строк как по абзацам и убираем ** **
  return text
    .split(/\n\s*\n/)
    .map((s) => stripMdBold(s.trim()))
    .filter(Boolean);
});
</script>

<style scoped>
.movie-descr p {
  margin: 0 0 8px;
  line-height: 1.4;
}

.movie-descr p:last-child {
  margin-bottom: 0;
}

.no-movie {
  text-align: center;
  padding: 60px 20px;
}

body.light-off {
  overflow: hidden;
}

.light-off-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.85);
  z-index: 9998;
  cursor: pointer;
}

#player-container.player-overlay {
  position: relative;
  z-index: 9999;
  background: #1d1d1d;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 0 25px rgba(0, 0, 0, 0.5);
}

.tabs-block__select button.active {
  background-color: #30b830;
  color: white;
}

.no-movie h1 {
  margin-bottom: 20px;
}

.sv-container {
  height: 760px;
}
@media (max-width: 768px) {
  .sv-container {
    height: 300px;
  }
}
@media (max-width: 425px) {
  .sv-container {
    height: 200px;
  }
}

.no-movie .btn {
  display: inline-block;
  padding: 12px 24px;
  background: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  margin-top: 20px;
}

/* Стили для оценок */
.page-rate-btn {
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  color: inherit;
}

.page-rate-btn:hover {
  opacity: 0.8;
}
.page-rate-btn.voted .fal {
  transform: scale(1.1);
}

/* Стили для комментариев */
.pagecontinue---comments {
  margin-top: 40px;
}
.comment-item {
  transition: margin-left 0.3s ease-in-out;
}
.form_for-comment--header {
  gap: 15px;
  margin-bottom: 15px;
}

.form_for-comment--input {
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.form_for-comment--input:focus {
  outline: none;
  border-color: #30b830;
  box-shadow: 0 0 0 2px rgba(56, 190, 56, 0.2);
}

.form_for-comment--editor {
  margin-bottom: 15px;
}

.form_for-comment--editor textarea {
  width: 100%;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
  min-height: 120px;
}

.form_for-comment--editor textarea:focus {
  outline: none;
  border-color: #30b830;
  box-shadow: 0 0 0 2px rgba(56, 190, 56, 0.2);
}

.form_for-comment--btn {
  padding: 12px 24px;
  background: #30b830;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.form_for-comment--btn:hover:not(:disabled) {
  background: #2ea02e;
}

.form_for-comment--btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form_for-comment--actions {
  display: flex;
  gap: 10px;
}

.cancel-btn {
  background-color: #6c757d;
}

.cancel-btn:hover {
  background-color: #5a6268;
}

.comment {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  background: white;
}

.comment.pos {
  border-left: 4px solid #30b830;
}

.comment.neg {
  border-left: 4px solid #ff6b6b;
}

.coment__header {
  margin-bottom: 15px;
}

.coment__author {
  font-weight: 600;
  color: #333;
}

.coment__date {
  color: #666;
  font-size: 14px;
}

.coment__text {
  line-height: 1.6;
  margin-bottom: 15px;
  color: #333;
}

.coment__tools {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.reply-btn {
  color: #666;
  font-size: 14px;
  cursor: pointer;
  text-decoration: none;
}

.reply-btn:hover {
  text-decoration: underline;
}

.ratingsOnComment {
  display: flex;
  align-items: center;
  gap: 10px;
}
.reply-form-container {
  margin-bottom: 15px;
}
.ratingtypeplusminus {
  font-weight: 600;
  color: #333;
}

.ratingsOnComment-btn {
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: all 0.2s ease;
  text-decoration: none;
}

.ratingsOnComment-btn:hover {
  background: #f5f5f5;
}

.ratingsOnComment-btn.thelike.voted {
  color: rgb(70, 209, 70);
}
.ratingsOnComment-btn.thedislike.voted {
  color: #ff6b6b;
}

.ratingsOnComment-btn.voted .fal {
  transform: scale(1.1);
}

.page-rate-btn.is-disabled {
  pointer-events: none;
  opacity: 0.6;
}

.message-info {
  background: #f8f9fa;
  border-radius: 6px;
  margin-bottom: 20px;
  color: #666;
  text-align: center;
}

.pagecontinue---comments-info {
  padding: 15px;
  background: #e3f2fd;
  border-radius: 6px;
  margin-bottom: 20px;
  color: #1976d2;
  text-align: center;
}

.video-fallback {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 802px;
  padding: 40px;
  background: #2d2d2d;
  border: 1px solid #444;
  border-radius: 8px;
  color: #ffffff;
  text-align: center;
  line-height: 1.7;
  font-size: 16px;
}

.video-fallback p {
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  font-size: 18px;
  line-height: 1.8;
  overflow-wrap: anywhere; /* перенос длинных слов/URL при необходимости */
}

.tabs-block__content.video-inside {
  position: relative;
}

.player-pane {
  position: relative;
  background: #141414;
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  overflow: hidden;
}

/* .player-loader {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  color: #f5f5f5;
  background: rgba(14, 14, 14, 0.86);
  backdrop-filter: blur(4px);
  z-index: 5;
  pointer-events: none;
  text-align: center;
  font-size: 18px;
}

.player-loader__spinner {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: 4px solid rgba(255, 255, 255, 0.14);
  border-top-color: #30b830;
  animation: player-loader-spin 0.9s linear infinite;
} */
@keyframes player-loader-spin {
  to {
    transform: rotate(360deg);
  }
}
.ratingsOnComment-btn.is-disabled {
  pointer-events: none;
  opacity: 0.6;
}
.pagecontinue---main.is-narrow-poster { grid-template-columns: 220px minmax(0, 1fr); }
@media (min-width: 2000px) { .pagecontinue---main.is-narrow-poster { grid-template-columns: 240px minmax(0, 1fr); } }

</style>
