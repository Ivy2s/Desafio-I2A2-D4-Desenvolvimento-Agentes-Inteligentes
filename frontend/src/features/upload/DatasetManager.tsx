import { useState } from 'react'
import type { WorkspaceData, WorkspaceDataset } from '../../contracts/workspace'
import { UploadDropzone } from './UploadDropzone'
import { UploadSteps } from './UploadSteps'
import { dataAssistantGateway } from '../../services/dataAssistantGateway'
import { workspaceGateway } from '../../services/workspaceGateway'
import '../../styles/dataset-manager.css'

interface DatasetManagerProps {
  workspace: WorkspaceData
  onQueryReady: (workspace: WorkspaceData) => void
}

export function DatasetManager({ workspace, onQueryReady }: DatasetManagerProps) {
  const [uploadState, setUploadState] = useState<'idle' | 'selected' | 'uploading' | 'error' | 'ready' | 'drag-active' | 'invalid-file'>('idle')
  const [selectedFile, setSelectedFile] = useState<File>()
  const [uploadError, setUploadError] = useState<string>()
  const [currentWorkspace, setCurrentWorkspace] = useState<WorkspaceData>(workspace)

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
    if (!selectedFile || uploadState === 'uploading') return
    setUploadError(undefined)
    setUploadState('uploading')
    try {
      const summary = await dataAssistantGateway.uploadDataset(selectedFile)
      // Add dataset to workspace
      const updatedWorkspace = await workspaceGateway.addDataset(
        currentWorkspace.workspaceId,
        summary.id
      )
      setCurrentWorkspace(updatedWorkspace)
      setUploadState('ready')
      setSelectedFile(undefined)
    } catch (error) {
      setUploadError(getUploadErrorMessage(error))
      setUploadState('error')
    }
  }

  const resetUpload = () => {
    setSelectedFile(undefined)
    setUploadError(undefined)
    setUploadState('idle')
  }

  return (
    <section className="dataset-manager">
      <div className="section-heading">
        <div>
          <span className="step-label">carregue seus datasets</span>
          <h2>Adicione CSV ou ZIP</h2>
        </div>
        <p>Adicione um ou mais datasets para análise.</p>
      </div>

      <div className="dataset-list">
        {currentWorkspace.datasets.length > 0 && (
          <div className="datasets-loaded">
            <h3>Datasets carregados ({currentWorkspace.datasets.length})</h3>
            <ul>
                {currentWorkspace.datasets.map((dataset: WorkspaceDataset) => (
                  <li key={dataset.datasetId} className="dataset-item">
                    <div className="dataset-item__header">
                      <span className="dataset-name">
                        {dataset.fileNames.length > 1
                          ? `${dataset.fileNames.length} arquivos CSV`
                          : dataset.name}
                      </span>
                      <span className="dataset-meta">{dataset.rows.toLocaleString('pt-BR')} registros</span>
                    </div>
                    {dataset.fileNames.length > 1 && (
                      <ul className="dataset-item__files" aria-label="Arquivos CSV deste upload">
                        {dataset.fileNames.map((fileName) => (
                          <li key={fileName}>
                            <span className="csv-mark">CSV</span>
                            {fileName}
                          </li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
            </ul>
            {currentWorkspace.datasets.length > 0 && (
              <button
                className="primary-button"
                onClick={() => onQueryReady(currentWorkspace)}
              >
                Fazer perguntas sobre estes dados
              </button>
            )}
          </div>
        )}
      </div>

      <div className="upload-section">
        <UploadSteps state={uploadState} />
        {uploadState === 'ready' && selectedFile ? (
          <div className="upload-success">
            <p>✓ {selectedFile.name} foi carregado com sucesso.</p>
            <button onClick={resetUpload} className="secondary-button">
              Carregar outro arquivo
            </button>
          </div>
        ) : (
          <UploadDropzone
            state={uploadState}
            file={selectedFile}
            error={uploadError}
            onFile={handleFile}
            onStart={handleStartUpload}
            onRemove={resetUpload}
            onDragState={(active) => {
              if (!selectedFile) setUploadState(active ? 'drag-active' : 'idle')
            }}
          />
        )}
      </div>
    </section>
  )
}

function getUploadErrorMessage(error: unknown) {
  if (!(error instanceof Error)) return 'Não foi possível enviar este arquivo.'
  if (error.message.includes('CSV') || error.message.includes('ZIP')) return 'Envie um arquivo CSV ou ZIP.'
  if (error.message.includes('excede')) return 'O arquivo excede o limite permitido.'
  if (error.message.includes('CSVs')) return 'Não foi possível preparar os CSVs deste arquivo.'
  if (error.message.includes('conectar')) return 'Não foi possível conectar ao servidor. Tente novamente.'
  return 'Não foi possível preparar o dataset. Tente novamente.'
}
