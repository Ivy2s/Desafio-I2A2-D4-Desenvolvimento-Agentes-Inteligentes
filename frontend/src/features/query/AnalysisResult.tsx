import type { QueryResponse } from '../../contracts/dataAssistant'
import { DataChart } from './DataChart'
import { DataTable } from './DataTable'
import { deriveVisualization } from './deriveVisualization'

interface AnalysisResultProps { result: QueryResponse }

export function AnalysisResult({ result }: AnalysisResultProps) {
  const table = result.data?.type === 'table' ? result.data : null
  const chart = table ? deriveVisualization(table) : null
  return <article className="analysis-result" aria-labelledby={`result-${result.id}`}><div className="result-kicker"><span className="result-icon">A</span><span>análise concluída</span>{(result.metadata?.executionTimeMs || result.metadata?.agent) && <span className="result-time">{result.metadata.executionTimeMs ? `${result.metadata.executionTimeMs}ms` : ''}{result.metadata?.executionTimeMs && result.metadata?.agent ? ' · ' : ''}{result.metadata?.agent}</span>}</div><h3 id={`result-${result.id}`}>{result.question}</h3><p className="result-answer">{result.answer}</p>{result.data?.type === 'count' && <div className="count-result" aria-label={`${result.data.value.toLocaleString('pt-BR')} registros`}><strong>{result.data.value.toLocaleString('pt-BR')}</strong><span>registros</span></div>}{table && <div className="result-table"><div className="result-subheading"><span>Dados relacionados</span><span>{table.returnedRows.toLocaleString('pt-BR')} linhas{table.truncated ? ' · resultado limitado' : ''}</span></div>{table.truncated && <p className="table-notice">Exibindo os primeiros {table.returnedRows.toLocaleString('pt-BR')} resultados retornados pela análise.</p>}{chart && <DataChart chart={chart} />}<DataTable table={table} /></div>}</article>
}
