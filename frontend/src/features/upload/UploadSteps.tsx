import type { UploadState } from '../../contracts/dataAssistant'

interface UploadStepsProps { state: UploadState }

const stepForState = (state: UploadState) => {
  if (state === 'idle' || state === 'drag-active' || state === 'invalid-file' || state === 'error') return 1
  if (state === 'selected' || state === 'uploading' || state === 'processing') return state === 'processing' ? 2 : 1
  return 3
}

export function UploadSteps({ state }: UploadStepsProps) {
  const current = stepForState(state)
  return (
    <ol className="upload-steps" aria-label="Etapas de preparação do dataset">
      {['Importar', 'Processar', 'Consultar'].map((label, index) => {
        const step = index + 1
        return <li className={step < current ? 'upload-step upload-step--done' : step === current ? 'upload-step upload-step--current' : 'upload-step'} key={label}>
          <span className="upload-step__number">{step < current ? '✓' : `0${step}`}</span><span>{label}</span>
        </li>
      })}
    </ol>
  )
}
