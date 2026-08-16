import { suggestedQuestionsList } from './suggestedQuestionsList'

interface SuggestedQuestionsProps {
  onSelect: (question: string) => void
}

export function SuggestedQuestions({ onSelect }: SuggestedQuestionsProps) {
  return <section className="suggestions" aria-labelledby="suggestions-title"><div className="suggestions__heading"><span id="suggestions-title">Comece por uma destas perguntas</span><span className="suggestions__hint">ou escreva a sua</span></div><div className="suggestions__list">{suggestedQuestionsList.map((question) => <button key={question} onClick={() => onSelect(question)}>{question}<span aria-hidden="true">↗</span></button>)}</div></section>
}
