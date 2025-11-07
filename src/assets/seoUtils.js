// Централизованные утилиты для работы с SEO

/**
 * Создает или обновляет тег в head
 */
export function upsertTag(selector, create) {
  if (typeof document === "undefined") return null;

  let el = document.head.querySelector(selector);
  if (!el) {
    el = create();
    document.head.appendChild(el);
  }
  return el;
}

/**
 * Устанавливает meta тег
 */
export function setMeta(name, content) {
  if (!content || typeof document === "undefined") return;

  upsertTag(`meta[name="${name}"]`, () => {
    const m = document.createElement("meta");
    m.setAttribute("name", name);
    return m;
  }).setAttribute("content", content);
}

/**
 * Устанавливает Open Graph meta тег
 */
export function setOg(property, content) {
  if (!content || typeof document === "undefined") return;

  upsertTag(`meta[property="${property}"]`, () => {
    const m = document.createElement("meta");
    m.setAttribute("property", property);
    return m;
  }).setAttribute("content", content);
}

/**
 * Устанавливает Twitter meta тег
 */
export function setTwitter(name, content) {
  if (!content || typeof document === "undefined") return;

  upsertTag(`meta[name="${name}"]`, () => {
    const m = document.createElement("meta");
    m.setAttribute("name", name);
    return m;
  }).setAttribute("content", content);
}

/**
 * Устанавливает canonical ссылку
 */
export function setCanonical(url) {
  if (!url || typeof document === "undefined") return;

  upsertTag('link[rel="canonical"]', () => {
    const l = document.createElement("link");
    l.setAttribute("rel", "canonical");
    return l;
  }).setAttribute("href", url);
}

/**
 * Устанавливает JSON-LD структурированные данные
 */
export function setJsonLd(id, obj) {
  if (typeof document === "undefined") return;

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

/**
 * Очищает текст от HTML тегов
 */
export function stripTags(html) {
  return String(html || "")
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Обрезает текст до указанной длины
 */
export function truncateText(text, maxLength = 300) {
  const str = String(text || "");
  return str.length <= maxLength
    ? str
    : str.slice(0, maxLength).replace(/\s+\S*$/, "") + "…";
}

/**
 * Комплексная функция для установки SEO данных фильма
 */
export function updateMovieSeo(movie, categoryTitle) {
  if (typeof window === "undefined" || !movie) return;

  const origin = window.location.origin;
  const pageUrl = `${origin}/${movie.category}/${movie.id}`;

  const isSerial =
    movie.category === "serialy" ||
    movie.category === "serials" ||
    !!movie.season ||
    !!movie.episode;

  const typeLabel =
    movie.category === "filmy"
      ? "фильм"
      : movie.category === "serialy" || movie.category === "serials"
      ? "сериал"
      : movie.category === "multfilmy"
      ? "мультфильм"
      : movie.category === "anime"
      ? "аниме"
      : "фильм";

  const metaParts = [];
  if (movie.year) metaParts.push(String(movie.year));
  const se = [];
  if (movie.season) {
    const s = String(movie.season).trim();
    se.push(/сезон/i.test(s) ? s : `${s} сезон`);
  }
  if (movie.episode) {
    const e = String(movie.episode).trim();
    se.push(/сер(ия|ии)/i.test(e) ? e : `${e} серия`);
  }
  if (se.length) metaParts.push(se.join(" "));
  const details = metaParts.length ? ` (${metaParts.join(", ")})` : "";

  const synopsis = stripTags(movie.description || "");
  const synopsisShort = truncateText(synopsis, 200);

  const titleFull = `${movie.title}${
    movie.year ? ` (${movie.year})` : ""
  } смотреть онлайн бесплатно в хорошем качестве`;
  const desc = isSerial
    ? `Смотреть ${typeLabel} ${movie.title} все серии подряд${details}. Описание: ${synopsisShort}`
    : `Смотреть ${typeLabel} ${movie.title}${details} онлайн в отличном качестве с русской озвучкой. Описание: ${synopsisShort}`;

  const posterAbs = movie.image
    ? movie.image.startsWith("http")
      ? movie.image
      : new URL(
          movie.image.startsWith("/") ? movie.image : `/${movie.image}`,
          origin
        ).href
    : undefined;
  const logoAbs = `${origin}/assets/ProsmotrZone_site/images/NewLogo.webp`;

  document.title = titleFull;
  setMeta("description", desc);
  setMeta("robots", "index,follow");

  setOg("og:type", isSerial ? "video.tv_show" : "video.movie");
  setOg("og:title", titleFull);
  setOg("og:description", desc);
  setOg("og:url", pageUrl);
  setOg("og:image", posterAbs || logoAbs);

  setTwitter(
    "twitter:card",
    posterAbs || logoAbs ? "summary_large_image" : "summary"
  );
  setTwitter("twitter:title", titleFull);
  setTwitter("twitter:description", desc);
  setTwitter("twitter:image", posterAbs || logoAbs);

  setCanonical(pageUrl);

  const ratingRaw = movie.imdbRating || movie.kpRating;
  const ratingNum = parseFloat(String(ratingRaw || "").replace(",", "."));
  const ldDesc = truncateText(synopsis, 300);

  const baseType = isSerial ? "TVSeries" : "Movie";
  const movieLd = {
    "@context": "https://schema.org",
    "@type": baseType,
    name: movie.title,
    datePublished: movie.year ? String(movie.year) : undefined,
    image: posterAbs || logoAbs,
    description: ldDesc,
    aggregateRating:
      Number.isFinite(ratingNum) && ratingNum > 0
        ? {
            "@type": "AggregateRating",
            ratingValue: ratingNum.toFixed(1),
            bestRating: "10",
            worstRating: "0",
          }
        : undefined,
  };
  setJsonLd("movie", movieLd);

  const breadcrumbs = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Главная", item: origin + "/" },
      {
        "@type": "ListItem",
        position: 2,
        name: categoryTitle || "Категория",
        item: `${origin}/${movie.category}`,
      },
      { "@type": "ListItem", position: 3, name: movie.title, item: pageUrl },
    ],
  };
  setJsonLd("breadcrumbs", breadcrumbs);
}
