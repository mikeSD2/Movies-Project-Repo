// Централизованные утилиты для работы с датами

const MONTH_MAP = {
  'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
  'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
  'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'
}

/**
 * Парсит русскую дату в формате "1 января 2024"
 * @param {string} dateString - дата для парсинга
 * @returns {Date|null} - объект Date или null
 */
export function parseRussianDate(dateString) {
  if (!dateString) return null
  
  const parts = String(dateString).split(' ')
  if (parts.length < 3) return null
  
  const day = String(parts[0]).padStart(2, '0')
  const month = MONTH_MAP[parts[1]]
  const year = parts[2]
  
  if (!month) return null
  
  const iso = `${year}-${month}-${day}`
  const date = new Date(iso)
  return isNaN(date.getTime()) ? null : date
}

/**
 * Проверяет, была ли дата сегодня или вчера
 * @param {Date} date - дата для проверки
 * @returns {boolean}
 */
export function isTodayOrYesterday(date) {
  if (!date) return false
  
  const todayStart = new Date()
  todayStart.setHours(0, 0, 0, 0)
  
  const yesterdayStart = new Date(todayStart)
  yesterdayStart.setDate(todayStart.getDate() - 1)
  
  return date >= yesterdayStart
}

/**
 * Проверяет, нужно ли скрывать фильм по дате премьеры
 * @param {string} premiere - строка с датой премьеры
 * @returns {boolean}
 */
export function shouldHideByPremiere(premiere) {
  const date = parseRussianDate(premiere)
  return date && isTodayOrYesterday(date)
}

/**
 * Проверяет, является ли фильм недавней премьерой
 * @param {object} movie - объект фильма
 * @returns {boolean}
 */
export function isRecentPremiere(movie) {
  const date = parseRussianDate(movie?.premiere)
  return !!(date && isTodayOrYesterday(date))
}
