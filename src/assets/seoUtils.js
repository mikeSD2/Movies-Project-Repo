// Централизованные утилиты для работы с SEO

/**
 * Создает или обновляет тег в head
 */
export function upsertTag(selector, create) {
  if (typeof document === 'undefined') return null
  
  let el = document.head.querySelector(selector)
  if (!el) {
    el = create()
    document.head.appendChild(el)
  }
  return el
}

/**
 * Устанавливает meta тег
 */
export function setMeta(name, content) {
  if (!content || typeof document === 'undefined') return
  
  upsertTag(`meta[name="${name}"]`, () => {
    const m = document.createElement('meta')
    m.setAttribute('name', name)
    return m
  }).setAttribute('content', content)
}

/**
 * Устанавливает Open Graph meta тег
 */
export function setOg(property, content) {
  if (!content || typeof document === 'undefined') return
  
  upsertTag(`meta[property="${property}"]`, () => {
    const m = document.createElement('meta')
    m.setAttribute('property', property)
    return m
  }).setAttribute('content', content)
}

/**
 * Устанавливает Twitter meta тег
 */
export function setTwitter(name, content) {
  if (!content || typeof document === 'undefined') return
  
  upsertTag(`meta[name="${name}"]`, () => {
    const m = document.createElement('meta')
    m.setAttribute('name', name)
    return m
  }).setAttribute('content', content)
}

/**
 * Устанавливает canonical ссылку
 */
export function setCanonical(url) {
  if (!url || typeof document === 'undefined') return
  
  upsertTag('link[rel="canonical"]', () => {
    const l = document.createElement('link')
    l.setAttribute('rel', 'canonical')
    return l
  }).setAttribute('href', url)
}

/**
 * Устанавливает JSON-LD структурированные данные
 */
export function setJsonLd(id, obj) {
  if (typeof document === 'undefined') return
  
  const sel = `script[type="application/ld+json"][data-id="${id}"]`
  let el = document.head.querySelector(sel)
  if (!el) {
    el = document.createElement('script')
    el.type = 'application/ld+json'
    el.setAttribute('data-id', id)
    document.head.appendChild(el)
  }
  el.textContent = JSON.stringify(obj)
}

/**
 * Очищает текст от HTML тегов
 */
export function stripTags(html) {
  return String(html || '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

/**
 * Обрезает текст до указанной длины
 */
export function truncateText(text, maxLength = 300) {
  const str = String(text || '')
  return str.length <= maxLength 
    ? str 
    : str.slice(0, maxLength).replace(/\s+\S*$/, '') + '…'
}

/**
 * Комплексная функция для установки SEO данных фильма
 */
export function updateMovieSeo(movie, categoryTitle) {
  if (typeof window === 'undefined' || !movie) return
  
  const origin = window.location.origin
  const pageUrl = `${origin}/${movie.category}/${movie.id}`
  const titleFull = `${movie.title} (${movie.year}) смотреть онлайн — LordFilms`
  const desc = truncateText(stripTags(movie.description || ''), 300)
  const posterAbs = movie.image 
    ? (movie.image.startsWith('http') ? movie.image : new URL(movie.image.startsWith('/') ? movie.image : `/${movie.image}`, origin).href)
    : undefined

  // Основные meta теги
  document.title = titleFull
  setMeta('description', desc)
  setMeta('robots', 'index,follow')

  // Open Graph
  setOg('og:type', 'video.movie')
  setOg('og:title', titleFull)
  setOg('og:description', desc)
  setOg('og:url', pageUrl)
  if (posterAbs) setOg('og:image', posterAbs)

  // Twitter
  setTwitter('twitter:card', posterAbs ? 'summary_large_image' : 'summary')
  setTwitter('twitter:title', titleFull)
  setTwitter('twitter:description', desc)
  if (posterAbs) setTwitter('twitter:image', posterAbs)

  // Canonical
  setCanonical(pageUrl)

  // JSON-LD: Movie
  const rating = movie.imdbRating || movie.kpRating
  const movieLd = {
    '@context': 'https://schema.org',
    '@type': 'Movie',
    name: movie.title,
    datePublished: movie.year ? String(movie.year) : undefined,
    image: posterAbs,
    aggregateRating: rating ? {
      '@type': 'AggregateRating',
      ratingValue: Number(rating),
      bestRating: 10,
      ratingCount: 100
    } : undefined,
    description: desc
  }
  setJsonLd('movie', movieLd)

  // JSON-LD: Breadcrumbs
  const breadcrumbs = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Главная', item: origin + '/' },
      { '@type': 'ListItem', position: 2, name: categoryTitle || 'Категория', item: `${origin}/${movie.category}` },
      { '@type': 'ListItem', position: 3, name: movie.title, item: pageUrl }
    ]
  }
  setJsonLd('breadcrumbs', breadcrumbs)
}
