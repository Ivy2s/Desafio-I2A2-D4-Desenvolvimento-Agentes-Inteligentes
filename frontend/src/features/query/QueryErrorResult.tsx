interface QueryErrorResultProps {
  question: string
  message: string
  onRetry: () => void
  disabled: boolean
  cooldownSeconds?: number
}

export function QueryErrorResult({ question, message, onRetry, disabled, cooldownSeconds = 0 }: QueryErrorResultProps) {
  return <article className="analysis-result" aria-label="Falha na consulta"><div className="result-kicker"><span className="result-icon">!</span><span>consulta não concluída</span></div><h3>{question}</h3><p className="result-answer query-error">{message}</p>{cooldownSeconds > 0 && <p className="query-error">Nova tentativa disponível em {cooldownSeconds}s.</p>}<button className="text-button" type="button" onClick={onRetry} disabled={disabled || cooldownSeconds > 0}>tentar novamente</button></article>
}
