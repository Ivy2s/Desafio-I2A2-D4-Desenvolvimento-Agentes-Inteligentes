import { useState } from 'react'
import type { DatasetSummary, QueryResponse, UploadState } from '../contracts/dataAssistant'
import { DatasetSummary as DatasetSummaryPanel } from '../features/dataset/DatasetSummary'
import { AnalysisResult } from '../features/query/AnalysisResult'
import { QueryComposer } from '../features/query/QueryComposer'
import { QueryErrorResult } from '../features/query/QueryErrorResult'
import { canSubmitQuery, normalizeQuestion } from '../features/query/queryRules'
import { getQueryErrorMessage } from '../features/query/queryErrorMessage'
import { SuggestedQuestions } from '../features/query/SuggestedQuestions'
import { UploadDropzone } from '../features/upload/UploadDropzone'
import { UploadSteps } from '../features/upload/UploadSteps'
import { DataAssistantApiError } from '../services/http/dataAssistantApiError'
import { dataAssistantGateway } from '../services/dataAssistantGateway'
import './app.css'

interface HistoryItem { id: string; datasetId: string; question: string; result?: QueryResponse; error?: string }

function Brand() {
  return <a className="brand" href="/" aria-label="Data Assistent início"><span className="brand__mark" aria-hidden="true"><i /><i /><i /></span><span>Data Assistent</span></a>
}

function App() {
  const [uploadState, setUploadState] = useState<UploadState>('idle')
  const [selectedFile, setSelectedFile] = useState<File>()
  const [uploadError, setUploadError] = useState<string>()
  const [dataset, setDataset] = useState<DatasetSummary>()
  const [view, setView] = useState<'upload' | 'workspace'>('upload')
  const [question, setQuestion] = useState('')
  const [querying, setQuerying] = useState(false)
  const [queryError, setQueryError] = useState<string>()
  const [history, setHistory] = useState<HistoryItem[]>([])

  const handleFile = (file: File) => {
    setUploadError(undefined)
    setSelectedFile(undefined)
    const lowerName = file.name.toLowerCase()
    if (!lowerName.endsWith('.zip') && !lowerName.endsWith('.csv')) {
      setUploadError('Este formato não é aceito. Escolha um arquivo .CSV ou .ZIP.')
      setUploadState('invalid-file')
      return
    }
    setSelectedFile(file)
    setUploadState('selected')
  }

  const handleStartUpload = async () => {
    if (!selectedFile) return
    setUploadError(undefined)
    setUploadState('uploading')
    try {
      const summary = await dataAssistantGateway.uploadDataset(selectedFile)
      setDataset(summary)
      setUploadState('ready')
    } catch (error) {
      setUploadError(getUploadErrorMessage(error))
      setUploadState('error')
    }
  }

  const resetUpload = () => {
    setSelectedFile(undefined)
    setDataset(undefined)
    setUploadError(undefined)
    setUploadState('idle')
    setView('upload')
    setHistory([])
    setQuestion('')
    setQueryError(undefined)
  }

  const runQuery = async (historyId: string, datasetId: string, value: string) => {
    setQuerying(true)
    setQueryError(undefined)
    try {
      const result = await dataAssistantGateway.queryDataset({ datasetId, question: value })
      setHistory((current) => current.map((item) => item.id === historyId ? { ...item, result, error: undefined } : item))
      setQuestion('')
    } catch (error) {
      const message = getQueryErrorMessage(error)
      setHistory((current) => current.map((item) => item.id === historyId ? { ...item, error: message } : item))
      setQueryError(message)
    } finally {
      setQuerying(false)
    }
  }

  const submitQuestion = (value: string) => {
    const activeDataset = dataset
    if (!canSubmitQuery(activeDataset?.id, value, querying) || !activeDataset) return
    const trimmedQuestion = normalizeQuestion(value)
    const historyId = crypto.randomUUID()
    setQuestion(trimmedQuestion)
    setHistory((current) => [{ id: historyId, datasetId: activeDataset.id, question: trimmedQuestion }, ...current])
    void runQuery(historyId, activeDataset.id, trimmedQuestion)
  }

  const retryQuestion = (item: HistoryItem) => {
    if (!dataset || querying || item.datasetId !== dataset.id) return
    setHistory((current) => current.map((entry) => entry.id === item.id ? { ...entry, error: undefined } : entry))
    void runQuery(item.id, item.datasetId, item.question)
  }

  if (view === 'workspace' && dataset) return <Workspace dataset={dataset} question={question} querying={querying} queryError={queryError} history={history} onQuestionChange={setQuestion} onSubmit={submitQuestion} onRetry={retryQuestion} onLoadAnother={resetUpload} />

  return <main className="app-shell upload-screen">
    <header className="topbar"><Brand /></header>
    <section className="hero" aria-labelledby="page-title"><div className="hero__copy"><p className="eyebrow"><span className="eyebrow__line" /> workspace de dados</p><h1 id="page-title">Pergunte aos seus <em>dados.</em></h1><p className="hero__lead">Transforme arquivos CSV em respostas claras. Comece enviando um dataset para preparar seu espaço de análise.</p></div><div className="hero__signal" aria-hidden="true"><span /><span /><span /><span /><span /></div></section>
     <section className="workspace upload-workspace" aria-labelledby="upload-title"><div className="section-heading"><div><span className="step-label">01 / iniciar</span><h2 id="upload-title">Adicione um dataset</h2></div><p>Um CSV ou ZIP com seus dados<br className="desktop-only" /> é tudo que precisamos.</p></div><UploadSteps state={uploadState} />
       {uploadState === 'ready' && dataset ? <DatasetSummaryPanel dataset={dataset} onExplore={() => setView('workspace')} /> : <UploadDropzone state={uploadState} file={selectedFile} error={uploadError} onFile={handleFile} onStart={handleStartUpload} onRemove={resetUpload} onDragState={(active) => { if (!selectedFile) setUploadState(active ? 'drag-active' : 'idle') }} />}
    </section>
    <footer className="footer"><span>Data Assistent</span><span className="footer__detail">feito para explorar, entender e decidir</span></footer>
  </main>
}

function getUploadErrorMessage(error: unknown) {
  if (!(error instanceof DataAssistantApiError)) return error instanceof Error ? error.message : 'Não foi possível enviar este arquivo.'
  if (error.code === 'unsupported_file_type') return 'Envie um arquivo CSV ou ZIP.'
  if (error.code === 'upload_too_large') return 'O arquivo excede o limite permitido.'
  if (['invalid_zip', 'unsafe_zip_entry', 'no_csv_files_found', 'zip_limit_exceeded', 'dataset_load_failed'].includes(error.code)) return 'Não foi possível preparar os CSVs deste arquivo.'
  if (error.code === 'network_error') return 'Não foi possível conectar ao servidor. Tente novamente.'
  return error.message
}

interface WorkspaceProps { dataset: DatasetSummary; question: string; querying: boolean; queryError?: string; history: HistoryItem[]; onQuestionChange: (value: string) => void; onSubmit: (question: string) => void; onRetry: (item: HistoryItem) => void; onLoadAnother: () => void }

function Workspace({ dataset, question, querying, queryError, history, onQuestionChange, onSubmit, onRetry, onLoadAnother }: WorkspaceProps) {
  return <main className="app-shell workspace-screen"><header className="topbar"><Brand /><div className="active-dataset"><span className="status-dot" /> <span className="active-dataset__name">{dataset.name}</span><span className="ready-label">ready</span></div><button className="text-button topbar__action" onClick={onLoadAnother}>carregar outro dataset <span aria-hidden="true">↗</span></button></header>
    <div className="workspace-layout"><aside className="dataset-sidebar" aria-labelledby="context-title"><div className="sidebar-heading"><span className="step-label">dataset ativo</span><span className="ready-status"><span className="status-dot" /> pronto</span></div><h1 id="context-title">{dataset.name}</h1><p className="sidebar-description">Dados de notas fiscais preparados para consulta.</p><dl className="sidebar-metrics"><div><dt>arquivos CSV</dt><dd>{dataset.csvFiles.length}</dd></div><div><dt>registros</dt><dd>{dataset.records.toLocaleString('pt-BR')}</dd></div><div><dt>colunas</dt><dd>{dataset.columns}</dd></div></dl><div className="sidebar-files"><p>arquivos detectados</p>{dataset.csvFiles.map((file) => <span key={file}><i className="csv-mark">CSV</i>{file}</span>)}</div><div className="sidebar-note"><span className="note-mark">i</span><p>As respostas desta sessão usam apenas o dataset ativo.</p></div></aside>
       <section className="query-area" aria-labelledby="query-title"><div className="query-intro"><p className="eyebrow"><span className="eyebrow__line" /> consulta natural</p><h2 id="query-title">O que você quer<br /><em>descobrir?</em></h2><p>Faça uma pergunta e receba uma leitura baseada nos seus dados.</p></div><QueryComposer value={question} busy={querying} error={queryError} onChange={onQuestionChange} onSubmit={onSubmit} />{querying && <div className="query-loading" role="status" aria-live="polite"><span className="loading-bars"><i /><i /><i /></span><span>Analisando dados</span><small>aguarde a resposta do servidor</small></div>}{history.length === 0 && !querying && <SuggestedQuestions onSelect={(value) => { onQuestionChange(value); onSubmit(value) }} />}{history.length > 0 && <section className="results" aria-labelledby="results-title"><div className="results-heading"><span id="results-title">Histórico da sessão</span><span>{history.length} {history.length === 1 ? 'consulta' : 'consultas'}</span></div>{history.map((item) => item.result ? <AnalysisResult key={item.id} result={item.result} /> : item.error ? <QueryErrorResult key={item.id} question={item.question} message={item.error} onRetry={() => onRetry(item)} disabled={querying} /> : <article key={item.id} className="analysis-result" aria-label="Consulta em andamento"><div className="result-kicker"><span className="result-icon">…</span><span>analisando consulta</span></div><h3>{item.question}</h3></article>)}</section>}</section>
      </div><footer className="footer"><span>Data Assistent</span><span className="footer__detail">respostas baseadas no dataset ativo</span></footer>
  </main>
}

export default App
