import { useEffect, useState } from 'react'
import type { WorkspaceData, WorkspaceQueryResponse, WorkspaceDataset } from '../../contracts/workspace'
import { workspaceGateway } from '../../services/workspaceGateway'
import { QueryComposer } from '../query/QueryComposer'
import { AnalysisResult } from '../query/AnalysisResult'
import type { QueryResponse } from '../../contracts/dataAssistant'
import { QueryErrorResult } from '../query/QueryErrorResult'
import { SuggestedQuestions } from '../query/SuggestedQuestions'
import '../../styles/workspace-query.css'

interface QueryHistory {
  id: string
  question: string
  result?: WorkspaceQueryResponse
  error?: string
}

interface WorkspaceQueryProps {
  workspace: WorkspaceData
  onBack: () => void
}

export function WorkspaceQuery({ workspace, onBack }: WorkspaceQueryProps) {
  const [question, setQuestion] = useState('')
  const [querying, setQuerying] = useState(false)
  const [queryError, setQueryError] = useState<string>()
  const [cooldownRemaining, setCooldownRemaining] = useState(0)
  const [history, setHistory] = useState<QueryHistory[]>([])

  useEffect(() => {
    if (cooldownRemaining <= 0) return
    const timer = window.setTimeout(() => {
      setCooldownRemaining((remaining) => Math.max(0, remaining - 1))
    }, 1000)
    return () => window.clearTimeout(timer)
  }, [cooldownRemaining])

  const submitQuestion = async (value: string) => {
    if (!value.trim() || querying || cooldownRemaining > 0) return

    const trimmedQuestion = value.trim()
    const historyId = crypto.randomUUID()
    setQuestion(trimmedQuestion)
    setHistory((current) => [{ id: historyId, question: trimmedQuestion }, ...current])
    setQueryError(undefined)

    setQuerying(true)
    try {
      const result = await workspaceGateway.queryWorkspace(workspace.workspaceId, {
        question: trimmedQuestion,
      })
      setHistory((current) =>
        current.map((item) =>
          item.id === historyId ? { ...item, result, error: undefined } : item,
        ),
      )
      setQuestion('')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro ao processar consulta'
      setHistory((current) =>
        current.map((item) => (item.id === historyId ? { ...item, error: message } : item)),
      )
      setQueryError(message)
      
      // Check for rate limit
      if ((error as any)?.code?.includes('rate_limit')) {
        setCooldownRemaining(60)
      }
    } finally {
      setQuerying(false)
    }
  }

  const retryQuestion = (item: QueryHistory) => {
    if (querying || cooldownRemaining > 0) return
    const newHistory = history.map((entry) =>
      entry.id === item.id ? { ...entry, error: undefined } : entry,
    )
    setHistory(newHistory)
    void submitQuestion(item.question)
  }

  return (
    <main className="workspace-query-screen">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Data Assistent início">
          <span className="brand__mark" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
          <span>Data Assistent</span>
        </a>
        <div className="active-workspace">
          <span className="status-dot" />
          <span className="workspace-name">{workspace.name}</span>
          <span className="ready-label">pronto</span>
        </div>
        <button className="text-button topbar__action" onClick={onBack}>
          gerenciar datasets <span aria-hidden="true">↗</span>
        </button>
      </header>

      <div className="workspace-layout">
        <aside className="workspace-sidebar" aria-labelledby="context-title">
          <div className="sidebar-heading">
            <span className="step-label">workspace ativo</span>
            <span className="ready-status">
              <span className="status-dot" /> pronto
            </span>
          </div>
          <h1 id="context-title">{workspace.name}</h1>
          <p className="sidebar-description">Datasets preparados para consulta.</p>

          <dl className="sidebar-metrics">
            <div>
              <dt>datasets</dt>
              <dd>{workspace.summary.files}</dd>
            </div>
            <div>
              <dt>registros</dt>
              <dd>{workspace.summary.rows.toLocaleString('pt-BR')}</dd>
            </div>
            <div>
              <dt>colunas</dt>
              <dd>{workspace.summary.columns}</dd>
            </div>
          </dl>

          <div className="sidebar-datasets">
            <p>datasets carregados</p>
            {workspace.datasets.flatMap((dataset: WorkspaceDataset) =>
              dataset.fileNames.length > 0
                ? dataset.fileNames.map((fileName) => (
                    <span key={`${dataset.datasetId}-${fileName}`}>
                      <i className="csv-mark">CSV</i>
                      {fileName}
                    </span>
                  ))
                : [
                    <span key={dataset.datasetId}>
                      <i className="csv-mark">CSV</i>
                      {dataset.name}
                    </span>,
                  ],
            )}
          </div>

          <div className="sidebar-note">
            <span className="note-mark">i</span>
            <p>As respostas desta sessão usam todos os datasets carregados.</p>
          </div>
        </aside>

        <section className="query-area" aria-labelledby="query-title">
          <div className="query-intro">
            <p className="eyebrow">
              <span className="eyebrow__line" /> consulta natural
            </p>
            <h2 id="query-title">
              O que você quer
              <br />
              <em>descobrir?</em>
            </h2>
            <p>Faça uma pergunta e receba uma leitura baseada em todos os seus dados.</p>
          </div>

          <QueryComposer
            value={question}
            busy={querying || cooldownRemaining > 0}
            error={queryError}
            onChange={setQuestion}
            onSubmit={submitQuestion}
          />

          {querying && (
            <div className="query-loading" role="status" aria-live="polite">
              <span className="loading-bars">
                <i />
                <i />
                <i />
              </span>
              <span>Analisando dados</span>
              <small>aguarde a resposta do servidor</small>
            </div>
          )}

          {history.length === 0 && !querying && (
            <SuggestedQuestions
              onSelect={(value) => {
                setQuestion(value)
                submitQuestion(value)
              }}
            />
          )}

          {history.length > 0 && (
            <section className="results" aria-labelledby="results-title">
              <div className="results-heading">
                <span id="results-title">Histórico da sessão</span>
                <span>
                  {history.length} {history.length === 1 ? 'consulta' : 'consultas'}
                </span>
              </div>
              {history.map((item) =>
                item.result ? (
                  (() => {
                    const normalized: QueryResponse = {
                      id: item.id,
                      question: item.question,
                      answer: item.result.answer,
                      data: (item.result.data as any) ?? null,
                    }
                    return <AnalysisResult key={item.id} result={normalized} />
                  })()
                ) : item.error ? (
                  <QueryErrorResult
                    key={item.id}
                    question={item.question}
                    message={item.error}
                    onRetry={() => retryQuestion(item)}
                    disabled={querying}
                    cooldownSeconds={cooldownRemaining}
                  />
                ) : (
                  <article key={item.id} className="analysis-result" aria-label="Consulta em andamento">
                    <div className="result-kicker">
                      <span className="result-icon">…</span>
                      <span>analisando consulta</span>
                    </div>
                    <h3>{item.question}</h3>
                  </article>
                ),
              )}
            </section>
          )}
        </section>
      </div>

      <footer className="footer">
        <span>Data Assistent</span>
        <span className="footer__detail">respostas baseadas em todos os datasets carregados</span>
      </footer>
    </main>
  )
}
