import type { DatasetSummary as DatasetSummaryData } from '../../contracts/dataAssistant'

interface DatasetSummaryProps { dataset: DatasetSummaryData; onExplore: () => void }

export function DatasetSummary({ dataset, onExplore }: DatasetSummaryProps) {
  return <section className="dataset-ready" aria-labelledby="dataset-ready-title">
    <div className="ready-heading"><span className="ready-icon" aria-hidden="true">✓</span><div><p className="step-label">dataset preparado</p><h2 id="dataset-ready-title">Tudo pronto para explorar</h2></div><span className="ready-status"><span className="status-dot" /> pronto</span></div>
    <div className="dataset-ready__body"><div><p className="dataset-name">{dataset.name}</p><p className="dataset-files">{dataset.csvFiles.length} arquivos CSV identificados</p></div><dl className="dataset-metrics"><div><dt>registros</dt><dd>{dataset.records.toLocaleString('pt-BR')}</dd></div><div><dt>colunas</dt><dd>{dataset.columns}</dd></div></dl><button className="button button--primary" onClick={onExplore}>Explorar dados <span aria-hidden="true">→</span></button></div>
    <div className="file-list" aria-label="Arquivos detectados">{dataset.csvFiles.map((file) => <span key={file}><span className="csv-mark">CSV</span>{file}</span>)}</div>
  </section>
}
