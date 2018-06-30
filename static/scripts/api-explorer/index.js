import getResults from './get-results.js'

getResults()

const form = document.getElementById('ax-form')

form.onsubmit = event => {
  event.preventDefault()
  getResults()
}
