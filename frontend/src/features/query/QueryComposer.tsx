interface QueryComposerProps {
  value: string
  busy: boolean
  error?: string
  onChange: (value: string) => void
  onSubmit: (question: string) => void
}

export function QueryComposer({ value, busy, error, onChange, onSubmit }: QueryComposerProps) {
  return <form className="query-composer" onSubmit={(event) => { event.preventDefault(); if (value.trim()) onSubmit(value.trim()) }}>
    <label htmlFor="query-input">Faça uma pergunta sobre o dataset</label>
    <div className="query-input-wrap">
      <textarea id="query-input" value={value} maxLength={4000} onChange={(event) => onChange(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); if (value.trim()) onSubmit(value.trim()) } }} placeholder="O que você quer descobrir nos seus dados?" rows={3} disabled={busy} aria-describedby={error ? 'query-error' : 'query-help'} aria-busy={busy} />
      <button className="send-button" type="submit" disabled={busy || !value.trim()} aria-label={busy ? 'Analisando pergunta' : 'Enviar pergunta'}>{busy ? <span className="mini-loader" aria-hidden="true" /> : <span aria-hidden="true">↑</span>}</button>
    </div>
    <div className="composer-foot"><span id={error ? 'query-error' : 'query-help'} className={error ? 'query-error' : ''} role={error ? 'alert' : undefined}>{error || 'Enter para enviar · Shift + Enter para nova linha'}</span><span>{value.length}/4000</span></div>
  </form>
}
