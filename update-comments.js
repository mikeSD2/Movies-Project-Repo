const fs = require('fs').promises
const path = require('path')

async function updateComments() {
  try {
    const dataPath = path.join(__dirname, 'movies-data.json')
    const data = JSON.parse(await fs.readFile(dataPath, 'utf8'))
    
    // Обновляем комментарии для каждого фильма
    data.movies.forEach(movie => {
      if (movie.comments && Array.isArray(movie.comments)) {
        movie.comments.forEach(comment => {
          // Добавляем поле userVote если его нет
          if (typeof comment.userVote === 'undefined') {
            comment.userVote = null
          }
          
          // Исправляем формат даты если она в ISO формате
          if (comment.date && comment.date.includes('T')) {
            try {
              const date = new Date(comment.date)
              comment.date = date.toLocaleDateString('ru-RU')
            } catch (error) {
              console.log(`Ошибка конвертации даты для комментария ${comment.id}:`, error)
            }
          }
        })
      }
    })
    
    // Записываем обновленные данные
    await fs.writeFile(dataPath, JSON.stringify(data, null, 2), 'utf8')
    console.log('✅ Комментарии обновлены: добавлено поле userVote и исправлен формат даты')
    
  } catch (error) {
    console.error('❌ Ошибка:', error)
  }
}

updateComments()
