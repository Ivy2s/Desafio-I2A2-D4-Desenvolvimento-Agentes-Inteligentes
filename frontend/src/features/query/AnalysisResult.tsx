import type { QueryResponse } from '../../contracts/dataAssistant'
import { DataChart } from './DataChart'
import { DataTable } from './DataTable'

interface AnalysisResultProps { result: QueryResponse }

export function AnalysisResult({ result }: AnalysisResultProps) {
  return <article className="analysis-result" aria-labelledby={`result-${result.id}`}><div className="result-kicker"><span className="result-icon">A</span><span>análise concluída</span>{(result.metadata?.executionTimeMs || result.metadata?.agent) && <span className="result-time">{result.metadata.executionTimeMs ? `${result.metadata.executionTimeMs}ms` : ''}{result.metadata?.executionTimeMs && result.metadata?.agent ? ' · ' : ''}{result.metadata?.agent}</span>}</div><h3 id={`result-${result.id}`}>{result.question}</h3><p className="result-answer">{result.answer}</p>{result.count !== undefined && <p className="result-subheading">Total encontrado: {result.count.toLocaleString('pt-BR')}</p>}{result.chart && <DataChart chart={result.chart} />}{result.table && <div className="result-table"><div className="result-subheading"><span>Dados relacionados</span><span>{result.table.rows.length} linhas{result.table.truncated ? ' · resultado limitado' : ''}</span></div><DataTable columns={result.table.columns} rows={result.table.rows} /></div>}</article>
}
