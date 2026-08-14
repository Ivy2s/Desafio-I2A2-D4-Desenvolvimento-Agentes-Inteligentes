import type { QueryResponse } from '../../contracts/dataAssistant'
import { DataChart } from './DataChart'
import { DataTable } from './DataTable'

interface AnalysisResultProps { result: QueryResponse }

export function AnalysisResult({ result }: AnalysisResultProps) {
  return <article className="analysis-result" aria-labelledby={`result-${result.id}`}><div className="result-kicker"><span className="result-icon">A</span><span>análise concluída</span><span className="result-time">{result.metadata?.executionTimeMs}ms · {result.metadata?.agent}</span></div><h3 id={`result-${result.id}`}>{result.question}</h3><p className="result-answer">{result.answer}</p>{result.chart && <DataChart chart={result.chart} />}{result.table && <div className="result-table"><div className="result-subheading"><span>Dados relacionados</span><span>{result.table.rows.length} linhas</span></div><DataTable columns={result.table.columns} rows={result.table.rows} /></div>}</article>
}
