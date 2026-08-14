import { useState } from 'react'
import type { DatasetSummary, QueryResponse, UploadState } from '../contracts/dataAssistant'
import { DatasetSummary as DatasetSummaryPanel } from '../features/dataset/DatasetSummary'
import { AnalysisResult } from '../features/query/AnalysisResult'
import { QueryComposer } from '../features/query/QueryComposer'
import { SuggestedQuestions } from '../features/query/SuggestedQuestions'
import { UploadDropzone } from '../features/upload/UploadDropzone'
import { UploadSteps } from '../features/upload/UploadSteps'
import { dataAssistantGateway } from '../services/dataAssistantGateway'
import './app.css'

interface HistoryItem { id: string; result: QueryResponse }

function Brand() {
  return <a className="brand" href="/" aria-label="Atlas início"><span className="brand__mark">A</span><span>atlas</span></a>
}

function App() {
  const [uploadState, setUploadState] = useState<UploadState>('idle')
  const [selectedFile, setSelectedFile] = useState<File>()
  const [uploadProgress, setUploadProgress] = useState(0)
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
    setUploadState('validating')
    window.setTimeout(() => {
      if (!file.name.toLowerCase().endsWith('.zip')) {
        setUploadError('Este formato não é aceito. Escolha um arquivo .ZIP.')
        setUploadState('invalid-file')
        return
      }
      setSelectedFile(file)
      setUploadState('selected')
    }, 280)
  }

  const handleStartUpload = async () => {
    if (!selectedFile) return
    setUploadError(undefined)
    setUploadProgress(4)
    setUploadState('uploading')
    const progressTimer = window.setInterval(() => setUploadProgress((current) => Math.min(current + 12, 92)), 150)
    try {
      const summary = await dataAssistantGateway.uploadDataset(selectedFile)
      window.clearInterval(progressTimer)
      setUploadProgress(100)
      setUploadState('processing')
      await new Promise((resolve) => window.setTimeout(resolve, 950))
      setDataset(summary)
      setUploadState('ready')
    } catch (error) {
      window.clearInterval(progressTimer)
      setUploadError(error instanceof Error ? error.message : 'Não foi possível processar este arquivo.')
      setUploadState('error')
    }
  }

  const resetUpload = () => {
    setSelectedFile(undefined)
    setDataset(undefined)
    setUploadError(undefined)
    setUploadProgress(0)
    setUploadState('idle')
    setView('upload')
    setHistory([])
    setQuestion('')
    setQueryError(undefined)
  }

  const submitQuestion = async (value: string) => {
    if (!dataset || querying || !value.trim()) return
    setQuestion(value)
    setQueryError(undefined)
    setQuerying(true)
    try {
      const result = await dataAssistantGateway.queryDataset({ datasetId: dataset.id, question: value.trim() })
      setHistory((current) => [{ id: result.id, result }, ...current])
      setQuestion('')
    } catch (error) {
      setQueryError(error instanceof Error ? error.message : 'Não foi possível concluir a consulta.')
    } finally {
      setQuerying(false)
    }
  }

  if (view === 'workspace' && dataset) return <Workspace dataset={dataset} question={question} querying={querying} queryError={queryError} history={history} onQuestionChange={setQuestion} onSubmit={submitQuestion} onLoadAnother={resetUpload} />

  return <main className="app-shell upload-screen">
    <header className="topbar"><Brand /><div className="topbar__status"><span className="status-dot" /> ambiente local <span className="status-divider" /> v0.2</div></header>
    <section className="hero" aria-labelledby="page-title"><div className="hero__copy"><p className="eyebrow"><span className="eyebrow__line" /> workspace de dados</p><h1 id="page-title">Pergunte aos seus <em>dados.</em></h1><p className="hero__lead">Transforme arquivos CSV em respostas claras. Comece enviando um dataset para preparar seu espaço de análise.</p></div><div className="hero__signal" aria-hidden="true"><span /><span /><span /><span /><span /></div></section>
    <section className="workspace upload-workspace" aria-labelledby="upload-title"><div className="section-heading"><div><span className="step-label">01 / iniciar</span><h2 id="upload-title">Adicione um dataset</h2></div><p>Um ZIP com seus CSVs e dicionário<br className="desktop-only" /> de dados é tudo que precisamos.</p></div><UploadSteps state={uploadState} />
      {uploadState === 'ready' && dataset ? <DatasetSummaryPanel dataset={dataset} onExplore={() => setView('workspace')} /> : <UploadDropzone state={uploadState} file={selectedFile} progress={uploadProgress} error={uploadError} onFile={handleFile} onStart={handleStartUpload} onRemove={resetUpload} onDragState={(active) => { if (!selectedFile && uploadState !== 'validating') setUploadState(active ? 'drag-active' : 'idle') }} />}
    </section>
    <footer className="footer"><span>Atlas Data Assistant</span><span className="footer__detail">feito para explorar, entender e decidir</span></footer>
  </main>
}

interface WorkspaceProps { dataset: DatasetSummary; question: string; querying: boolean; queryError?: string; history: HistoryItem[]; onQuestionChange: (value: string) => void; onSubmit: (question: string) => void; onLoadAnother: () => void }

function Workspace({ dataset, question, querying, queryError, history, onQuestionChange, onSubmit, onLoadAnother }: WorkspaceProps) {
  return <main className="app-shell workspace-screen"><header className="topbar"><Brand /><div className="active-dataset"><span className="status-dot" /> <span className="active-dataset__name">{dataset.name}</span><span className="ready-label">ready</span></div><button className="text-button topbar__action" onClick={onLoadAnother}>carregar outro dataset <span aria-hidden="true">↗</span></button></header>
    <div className="workspace-layout"><aside className="dataset-sidebar" aria-labelledby="context-title"><div className="sidebar-heading"><span className="step-label">dataset ativo</span><span className="ready-status"><span className="status-dot" /> pronto</span></div><h1 id="context-title">{dataset.name}</h1><p className="sidebar-description">Dados de notas fiscais preparados para consulta.</p><dl className="sidebar-metrics"><div><dt>arquivos CSV</dt><dd>{dataset.csvFiles.length}</dd></div><div><dt>registros</dt><dd>{dataset.records.toLocaleString('pt-BR')}</dd></div><div><dt>colunas</dt><dd>{dataset.columns}</dd></div></dl><div className="sidebar-files"><p>arquivos detectados</p>{dataset.csvFiles.map((file) => <span key={file}><i className="csv-mark">CSV</i>{file}</span>)}</div><div className="sidebar-note"><span className="note-mark">i</span><p>As respostas desta sessão usam apenas o dataset ativo.</p></div></aside>
      <section className="query-area" aria-labelledby="query-title"><div className="query-intro"><p className="eyebrow"><span className="eyebrow__line" /> consulta natural</p><h2 id="query-title">O que você quer<br /><em>descobrir?</em></h2><p>Faça uma pergunta e receba uma leitura baseada nos seus dados.</p></div><QueryComposer value={question} busy={querying} error={queryError} onChange={onQuestionChange} onSubmit={onSubmit} />{querying && <div className="query-loading" role="status" aria-live="polite"><span className="loading-bars"><i /><i /><i /></span><span>Analisando dados</span><small>organizando uma resposta demonstrativa</small></div>}{history.length === 0 && !querying && <SuggestedQuestions onSelect={(value) => { onQuestionChange(value); onSubmit(value) }} />}{history.length > 0 && <section className="results" aria-labelledby="results-title"><div className="results-heading"><span id="results-title">Histórico da sessão</span><span>{history.length} {history.length === 1 ? 'consulta' : 'consultas'}</span></div>{history.map((item) => <AnalysisResult key={item.id} result={item.result} />)}</section>}</section>
    </div><footer className="footer"><span>Atlas Data Assistant</span><span className="footer__detail">mock de desenvolvimento · sem conexão externa</span></footer>
  </main>
}

export default App
