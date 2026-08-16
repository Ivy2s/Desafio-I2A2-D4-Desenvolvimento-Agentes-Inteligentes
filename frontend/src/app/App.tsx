import { useEffect, useState } from 'react'
import type { WorkspaceData } from '../contracts/workspace'
import { DatasetManager } from '../features/upload/DatasetManager'
import { WorkspaceQuery } from '../features/workspace/WorkspaceQuery'
import { workspaceGateway } from '../services/workspaceGateway'
import './app.css'

type View = 'workspace-select' | 'dataset-manager' | 'query'

function App() {
  const [view, setView] = useState<View>('workspace-select')
  const [workspace, setWorkspace] = useState<WorkspaceData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>()
  const [workspaceName, setWorkspaceName] = useState('')

  const handleCreateWorkspace = async () => {
    if (!workspaceName.trim()) return
    setLoading(true)
    setError(undefined)
    try {
      const newWorkspace = await workspaceGateway.createWorkspace(workspaceName.trim())
      setWorkspace(newWorkspace)
      setView('dataset-manager')
      setWorkspaceName('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar workspace')
    } finally {
      setLoading(false)
    }
  }

  const handleQueryReady = (ws: WorkspaceData) => {
    setWorkspace(ws)
    setView('query')
  }

  const handleBack = () => {
    if (workspace) {
      setView('dataset-manager')
    }
  }

  function Brand() {
    return (
      <a className="brand" href="/" aria-label="Data Assistent início">
        <span className="brand__mark" aria-hidden="true">
          <i />
          <i />
          <i />
        </span>
        <span>Data Assistent</span>
      </a>
    )
  }

  if (view === 'dataset-manager' && workspace) {
    return <DatasetManager workspace={workspace} onLoadAnother={() => setView('workspace-select')} onQueryReady={handleQueryReady} />
  }

  if (view === 'query' && workspace) {
    return <WorkspaceQuery workspace={workspace} onBack={handleBack} />
  }

  return (
    <main className="app-shell upload-screen">
      <header className="topbar">
        <Brand />
      </header>

      <section className="hero" aria-labelledby="page-title">
        <div className="hero__copy">
          <p className="eyebrow">
            <span className="eyebrow__line" /> workspace de dados
          </p>
          <h1 id="page-title">
            Pergunte aos seus <em>dados.</em>
          </h1>
          <p className="hero__lead">
            Transforme múltiplos arquivos CSV em respostas claras. Comece criando um workspace e adicionando seus datasets.
          </p>
        </div>
        <div className="hero__signal" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
          <span />
        </div>
      </section>

      <section className="workspace upload-workspace" aria-labelledby="workspace-title">
        <div className="section-heading">
          <div>
            <span className="step-label">01 / começar</span>
            <h2 id="workspace-title">Crie um workspace</h2>
          </div>
          <p>
            Comece a análise criando um novo espaço de trabalho.
            <br className="desktop-only" />
            Depois adicione seus datasets.
          </p>
        </div>

        <div className="workspace-creation">
          <div className="input-group">
            <input
              type="text"
              placeholder="Digite o nome do seu workspace"
              value={workspaceName}
              onChange={(e) => setWorkspaceName(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') handleCreateWorkspace()
              }}
              disabled={loading}
            />
            <button
              onClick={handleCreateWorkspace}
              disabled={loading || !workspaceName.trim()}
              className="primary-button"
            >
              {loading ? 'Criando...' : 'Criar Workspace'}
            </button>
          </div>
          {error && <div className="error-message">{error}</div>}
        </div>
      </section>

      <footer className="footer">
        <span>Data Assistent</span>
        <span className="footer__detail">feito para explorar, entender e decidir</span>
      </footer>
    </main>
  )
}

export default App
