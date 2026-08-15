import type { ChartModel } from './deriveVisualization'
import { formatCellValue, labelForColumn } from './tableFormatting'

interface DataChartProps { chart: ChartModel }

const numberValue = (value: unknown) => typeof value === 'number' && Number.isFinite(value) ? value : null
const textValue = (value: unknown) => String(value ?? '')
const compactNumber = (value: number) => Math.abs(value) >= 1_000_000 ? `${(value / 1_000_000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} mi` : Math.abs(value) >= 1000 ? `${(value / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} mil` : value.toLocaleString('pt-BR')

export function DataChart({ chart }: DataChartProps) {
  const width = 620; const height = 220; const padding = { top: 20, right: 18, bottom: 42, left: 48 }
  const pointsData = chart.rows.map((item) => ({ item, value: numberValue(item[chart.valueKey]) })).filter((point): point is { item: Record<string, unknown>; value: number } => point.value !== null)
  if (pointsData.length === 0) return null
  const max = Math.max(...pointsData.map((point) => point.value), 1)
  const plotWidth = width - padding.left - padding.right; const plotHeight = height - padding.top - padding.bottom
  const points = pointsData.map(({ item, value }, index) => ({ x: padding.left + (pointsData.length === 1 ? plotWidth / 2 : index * plotWidth / (pointsData.length - 1)), y: padding.top + plotHeight - value / max * plotHeight, label: textValue(item[chart.categoryKey]), value }))
  const linePath = points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ')
  const title = `${labelForColumn(chart.valueKey)} por ${labelForColumn(chart.categoryKey)}`
  return <div className="chart-wrap"><div className="chart-title"><span>{title}</span><span className="chart-legend"><i /> {labelForColumn(chart.valueKey)}</span></div><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Visualização: ${title}`}>
    {[0, .5, 1].map((ratio) => <g key={ratio}><line x1={padding.left} x2={width - padding.right} y1={padding.top + plotHeight * ratio} y2={padding.top + plotHeight * ratio} className="chart-grid" /><text x={padding.left - 8} y={padding.top + plotHeight * ratio + 3} className="chart-y-label">{compactNumber(Math.round(max * (1 - ratio)))}</text></g>)}
    {chart.type === 'bar' ? points.map((point) => <g key={`${point.label}-${point.x}`}><title>{`${textValue(point.label)}: ${formatCellValue(point.value)}`}</title><rect x={point.x - Math.min(22, plotWidth / points.length / 3)} y={point.y} width={Math.min(44, plotWidth / points.length / 1.7)} height={padding.top + plotHeight - point.y} rx="3" className="chart-bar" /><text x={point.x} y={height - 16} textAnchor="middle" className="chart-label">{point.label.length > 12 ? `${point.label.slice(0, 11)}…` : point.label}</text></g>) : <><path d={linePath} className="chart-line" />{points.map((point) => <g key={`${point.label}-${point.x}`}><title>{`${textValue(point.label)}: ${formatCellValue(point.value)}`}</title><circle cx={point.x} cy={point.y} r="4" className="chart-point" /><text x={point.x} y={height - 16} textAnchor="middle" className="chart-label">{point.label}</text></g>)}</>}
  </svg></div>
}
