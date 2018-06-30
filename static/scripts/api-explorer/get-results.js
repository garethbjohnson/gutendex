const ERROR_MESSAGE = 'There was an error. Please check the input and the docs below.'

export default function getResults() {
  const urlElement = document.getElementById('ax-url')

  const resultArea = document.getElementById('ax-results')
  resultArea.textContent = 'Loading...'

  fetch(urlElement.value)
    .then(response => response.json())
    .then(object => resultArea.textContent = JSON.stringify(object, null, 2))
    .catch(failureReason => resultArea.textContent = ERROR_MESSAGE)
}
