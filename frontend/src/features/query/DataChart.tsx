import type { QueryResponse } from '../../contracts/dataAssistant'

interface DataChartProps { chart: NonNullable<QueryResponse['chart']> }

const numberValue = (value: unknown) => typeof value === 'number' ? value : Number(value) || 0
const textValue = (value: unknown) => String(value ?? '')
const compactNumber = (value: number) => value >= 1000 ? `${Math.round(value / 1000)}k` : String(value)

export function DataChart({ chart }: DataChartProps) {
  const width = 620; const height = 220; const padding = { top: 20, right: 18, bottom: 42, left: 48 }
  const max = Math.max(...chart.data.map((item) => numberValue(item[chart.yKey])), 1)
  const plotWidth = width - padding.left - padding.right; const plotHeight = height - padding.top - padding.bottom
  const points = chart.data.map((item, index) => ({ x: padding.left + (chart.data.length === 1 ? plotWidth / 2 : index * plotWidth / (chart.data.length - 1)), y: padding.top + plotHeight - numberValue(item[chart.yKey]) / max * plotHeight, label: textValue(item[chart.xKey]), value: numberValue(item[chart.yKey]) }))
  const linePath = points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ')
  return <div className="chart-wrap"><div className="chart-title"><span>{chart.title}</span><span className="chart-legend"><i /> valor simulado</span></div><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={chart.title || 'Gráfico de dados'}>
    {[0, .5, 1].map((ratio) => <g key={ratio}><line x1={padding.left} x2={width - padding.right} y1={padding.top + plotHeight * ratio} y2={padding.top + plotHeight * ratio} className="chart-grid" /><text x={padding.left - 8} y={padding.top + plotHeight * ratio + 3} className="chart-y-label">{compactNumber(Math.round(max * (1 - ratio)))}</text></g>)}
    {chart.type === 'bar' ? points.map((point) => <g key={point.label}><rect x={point.x - Math.min(22, plotWidth / chart.data.length / 3)} y={point.y} width={Math.min(44, plotWidth / chart.data.length / 1.7)} height={padding.top + plotHeight - point.y} rx="3" className="chart-bar" /><text x={point.x} y={height - 16} textAnchor="middle" className="chart-label">{point.label.length > 12 ? `${point.label.slice(0, 11)}…` : point.label}</text></g>) : <><path d={linePath} className="chart-line" />{points.map((point) => <g key={point.label}><circle cx={point.x} cy={point.y} r="4" className="chart-point" /><text x={point.x} y={height - 16} textAnchor="middle" className="chart-label">{point.label}</text></g>)}</>}
  </svg></div>
}
