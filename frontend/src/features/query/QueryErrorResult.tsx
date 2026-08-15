interface QueryErrorResultProps {
  question: string
  message: string
  onRetry: () => void
  disabled: boolean
}

export function QueryErrorResult({ question, message, onRetry, disabled }: QueryErrorResultProps) {
  return <article className="analysis-result" aria-label="Falha na consulta"><div className="result-kicker"><span className="result-icon">!</span><span>consulta não concluída</span></div><h3>{question}</h3><p className="result-answer query-error">{message}</p><button className="text-button" type="button" onClick={onRetry} disabled={disabled}>tentar novamente</button></article>
}
