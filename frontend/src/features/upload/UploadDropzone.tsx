import { useRef, type DragEvent, type ChangeEvent } from 'react'
import type { UploadState } from '../../contracts/dataAssistant'

interface UploadDropzoneProps {
  state: UploadState
  file?: File
  progress?: number
  error?: string
  onFile: (file: File) => void
  onStart: () => void
  onRemove: () => void
  onDragState: (active: boolean) => void
}

const formatSize = (bytes: number) => bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`

export function UploadDropzone({ state, file, progress = 0, error, onFile, onStart, onRemove, onDragState }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const isBusy = state === 'validating' || state === 'uploading' || state === 'processing'

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    onDragState(false)
    const file = event.dataTransfer.files[0]
    if (file) onFile(file)
  }

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) onFile(file)
  }

  return (
    <div
      className={`dropzone ${state === 'drag-active' ? 'dropzone--active' : ''} ${isBusy ? 'dropzone--busy' : ''}`}
      onDragEnter={(event) => { event.preventDefault(); onDragState(true) }}
      onDragOver={(event) => event.preventDefault()}
      onDragLeave={(event) => { if (event.currentTarget === event.target) onDragState(false) }}
      onDrop={handleDrop}
      role="region"
      aria-label="Área para envio do dataset"
      aria-busy={isBusy}
    >
      <input ref={inputRef} type="file" accept=".zip,application/zip" onChange={handleChange} hidden />
      <div className="upload-mark" aria-hidden="true"><span /></div>
      {state === 'selected' && file ? (
        <div className="selected-file">
          <p className="dropzone__title">{file.name}</p>
          <p className="dropzone__hint"><span className="zip-badge">ZIP</span> {formatSize(file.size)} · arquivo selecionado</p>
          <div className="selected-file__actions"><button className="button button--primary" onClick={onStart}>Iniciar upload <span aria-hidden="true">→</span></button><button className="text-button" onClick={onRemove}>remover e escolher outro</button></div>
        </div>
      ) : isBusy ? (
        <>
          <p className="dropzone__title">{state === 'uploading' ? 'Enviando seu arquivo' : 'Preparando seus dados'}</p>
          <p className="dropzone__hint">{state === 'processing' ? 'Organizando o espaço para sua consulta' : 'Comportamento simulado de desenvolvimento'}</p>
          <div className="progress-track" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={state === 'processing' ? 100 : progress} aria-label={state === 'processing' ? 'Processamento simulado em andamento' : `${progress}% do upload simulado`}><span style={{ width: `${Math.max(progress, 8)}%` }} /></div>
          <p className="progress-label">{state === 'processing' ? 'Lendo arquivos · identificando estrutura' : `${progress}% · upload simulado`}</p>
        </>
      ) : (
        <>
          <p className="dropzone__title">Solte seu arquivo ZIP aqui</p>
          <p className="dropzone__hint">ou <button className="inline-button" onClick={() => inputRef.current?.click()}>selecione do computador</button></p>
          <p className="dropzone__meta">somente .ZIP <span>até 500 MB</span></p>
        </>
      )}
      {state === 'invalid-file' && <p className="file-note file-note--error" role="alert">{error || 'Escolha um arquivo ZIP para continuar.'} <button className="inline-button" onClick={() => inputRef.current?.click()}>tentar novamente</button></p>}
      {state === 'error' && <p className="file-note file-note--error" role="alert">{error || 'Não foi possível preparar o arquivo.'} <button className="inline-button" onClick={onStart}>tentar novamente</button></p>}
      {!isBusy && state !== 'selected' && <span className="dropzone__size">CSV + dicionário · ZIP</span>}
    </div>
  )
}
