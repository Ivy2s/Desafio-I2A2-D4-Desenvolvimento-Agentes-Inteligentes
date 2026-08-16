const suggestedQuestions = [
  'Qual fornecedor recebeu o maior valor no período?',
  'Qual produto apresentou o maior volume comprado?',
  'Qual foi o total gasto em cada mês?',
  'Quais foram os cinco maiores fornecedores?',
  'Qual categoria apresentou maior crescimento nas compras?',
]

interface SuggestedQuestionsProps {
  onSelect: (question: string) => void
}

export function SuggestedQuestions({ onSelect }: SuggestedQuestionsProps) {
  return (
    <section className="suggestions" aria-labelledby="suggestions-title">
      <div className="suggestions__heading">
        <span id="suggestions-title">Comece por uma destas perguntas</span>
        <span className="suggestions__hint">ou escreva a sua</span>
      </div>

      <div className="suggestions__list">
        {suggestedQuestions.map((question) => (
          <button key={question} onClick={() => onSelect(question)}>
            {question}
            <span aria-hidden="true">↗</span>
          </button>
        ))}
      </div>
    </section>
  )
}
