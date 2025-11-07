import { computed } from 'vue'
import { parseRussianDate } from './dateUtils.js'

// Константы для фильтрации
export const ASIAN_KEYWORDS = [
  'южная корея', 'корея', 'северная корея', 'япония', 'китай', 'тайвань', 
  'гонконг', 'таиланд', 'индонезия', 'малайзия', 'вьетнам', 'сингапур', 'филиппины'
]

/**
 * Проверяет, является ли страна азиатской
 */
export function isAsianCountry(countryStr) {
  if (!countryStr) return false
  const s = String(countryStr).toLowerCase()
  return ASIAN_KEYWORDS.some(k => s.includes(k))
}

/**
 * Проверяет, является ли страна турецкой
 */
export function isTurkish(countryStr) {
  return /турция/i.test(countryStr || '')
}

/**
 * Базовый фильтр для всех фильмов
 */
export function createBaseFilter() {
  return (movie) => {
    if (movie.id === 'index') return false

    // Фильтрация по наличию IMDb рейтинга
    if (!movie.imdbRating) return false
    
    // Фильтрация по стране
    if (movie.country) {
      const country = movie.country.toLowerCase()
      if (country.includes('индия') || country.includes('пакистан')) {
        return false
      }
    }
    
    return true
  }
}

/**
 * Создает функцию сортировки
 */
export function createSorter(sortBy) {
  return (a, b) => {
    switch (sortBy) {
      case 'year':
        return b.year - a.year
      case 'rating': {
        const ratingA = Math.max(a.imdbRating || 0, a.kpRating || 0)
        const ratingB = Math.max(b.imdbRating || 0, b.kpRating || 0)
        return ratingB - ratingA
      }
      case 'popularity':
        return (b.popularity || 0) - (a.popularity || 0)
      case 'title':
        return a.title.localeCompare(b.title)
      case 'latest': {
        const dateA = parseRussianDate(a.premiere)?.getTime() || 0
        const dateB = parseRussianDate(b.premiere)?.getTime() || 0
        return dateB - dateA
      }
      default:
        return 0
    }
  }
}

/**
 * Фильтрация по временному диапазону
 */
export function createTimeRangeFilter(days) {
  const cutoffDate = new Date()
  cutoffDate.setDate(cutoffDate.getDate() - days)
  
  return (movie) => {
    const premiereDate = parseRussianDate(movie.premiere)
    return premiereDate && premiereDate >= cutoffDate
  }
}

/**
 * Composable для работы с популярными фильмами
 */
export function usePopularMovies(allMovies, count = 12) {
  return computed(() => {
    const thirtyDaysAgo = new Date()
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
    
    // Получаем недавние фильмы
    const recentMovies = allMovies.value.filter(movie => {
      const premiereDate = parseRussianDate(movie.premiere)
      return premiereDate && premiereDate >= thirtyDaysAgo
    })
    
    // Сортируем по популярности
    let popularRecent = []
    if (recentMovies.length > 0) {
      popularRecent = recentMovies
        .sort((a, b) => (b.popularity || 0) - (a.popularity || 0))
        .slice(0, count)
    }
    
    // Дополняем общими популярными, если недостаточно
    if (popularRecent.length < count) {
      const recentIds = new Set(popularRecent.map(m => m.id))
      const additionalMovies = allMovies.value
        .filter(movie => !recentIds.has(movie.id))
        .sort((a, b) => (b.popularity || 0) - (a.popularity || 0))
        .slice(0, count - popularRecent.length)
      
      return [...popularRecent, ...additionalMovies]
    }
    
    return popularRecent
  })
}

/**
 * Composable для фильтрации по категории с различными сортировками
 */
export function useCategoryMovies(allMovies, category, sortBy, timeRange = 365) {
  return computed(() => {
    const categoryVal = typeof category === 'string' ? category : (category && category.value != null ? category.value : null)
    const sortVal = typeof sortBy === 'string' ? sortBy : (sortBy?.value ?? 'latest')

    let filtered = allMovies.value
    if (categoryVal) {
      filtered = filtered.filter(movie => movie.category === categoryVal)
    }

    // Применяем временной фильтр для некоторых сортировок
    if (['latest', 'popular'].includes(sortVal)) {
      filtered = filtered.filter(createTimeRangeFilter(timeRange))
    } else if (sortVal === 'rating') {
      filtered = filtered.filter(createTimeRangeFilter(730)) // 2 года для рейтинга
    }

    // Сортируем
    filtered.sort(createSorter(sortVal))

    return filtered.slice(0, 24)
  })
}

/**
 * Composable для специальных фильтров (дорамы, турецкие сериалы)
 */
export function useSpecialFilters(allMovies) {
  const doramas = computed(() => 
    allMovies.value.filter(m => 
      m.category === 'serialy' && 
      isAsianCountry(m.country) && 
      !isTurkish(m.country)
    )
  )
  
  const turkishSeries = computed(() =>
    allMovies.value.filter(m => 
      m.category === 'serialy' && 
      isTurkish(m.country)
    )
  )
  
  return { doramas, turkishSeries }
}
