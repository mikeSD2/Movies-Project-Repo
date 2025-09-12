const fs = require('fs').promises
const path = require('path')

async function addCommentsField() {
  try {
    const dataPath = path.join(__dirname, 'movies-data.json')
    const data = JSON.parse(await fs.readFile(dataPath, 'utf8'))
    
    // Добавляем поле comments для каждого фильма
    data.movies.forEach(movie => {
      if (!movie.comments) {
        movie.comments = []
      }
    })
    
    // Записываем обновленные данные
    await fs.writeFile(dataPath, JSON.stringify(data, null, 2), 'utf8')
    console.log('✅ Поле comments добавлено для всех фильмов')
    
  } catch (error) {
    console.error('❌ Ошибка:', error)
  }
}

addCommentsField()
