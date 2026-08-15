import type { ChartModel } from './deriveVisualization'
import { labelForColumn } from './tableFormatting'
import { chartAxisValue, chartTicks, chartTooltipValue } from './chartFormatting'

interface DataChartProps { chart: ChartModel }

const numberValue = (value: unknown) => typeof value === 'number' && Number.isFinite(value) ? value : null
const textValue = (value: unknown) => String(value ?? '')

const truncateLabel = (label: string, length: number) => label.length > length ? `${label.slice(0, length - 1)}…` : label

export function DataChart({ chart }: DataChartProps) {
  const width = 720; const height = 330; const padding = { top: 24, right: 18, bottom: 58, left: 94 }
  const pointsData = chart.rows.map((item) => ({ item, value: numberValue(item[chart.valueKey]) })).filter((point): point is { item: Record<string, unknown>; value: number } => point.value !== null)
  if (pointsData.length === 0) return null
  const ticks = chartTicks(pointsData.map((point) => point.value), chart.type)
  const domainMin = ticks[0]
  const domainMax = ticks[ticks.length - 1]
  const plotWidth = width - padding.left - padding.right; const plotHeight = height - padding.top - padding.bottom
  const valueToY = (value: number) => padding.top + plotHeight - (value - domainMin) / (domainMax - domainMin) * plotHeight
  const points = pointsData.map(({ item, value }, index) => ({ x: padding.left + (pointsData.length === 1 ? plotWidth / 2 : index * plotWidth / (pointsData.length - 1)), y: valueToY(value), label: textValue(item[chart.categoryKey]), value }))
  const linePath = points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ')
  const title = `${labelForColumn(chart.valueKey)} por ${labelForColumn(chart.categoryKey)}`
  return <div className="chart-wrap"><div className="chart-title"><span>{title}</span><span className="chart-legend"><i /> {labelForColumn(chart.valueKey)}</span></div><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Visualização: ${title}`}>
    {ticks.map((tick) => <g key={tick}><line x1={padding.left} x2={width - padding.right} y1={valueToY(tick)} y2={valueToY(tick)} className="chart-grid" /><text x={padding.left - 12} y={valueToY(tick) + 4} className="chart-y-label">{chartAxisValue(tick, chart.valueKey)}</text></g>)}
    {chart.type === 'bar' ? points.map((point) => <g key={`${point.label}-${point.x}`} aria-label={`${point.label}: ${chartTooltipValue(point.value, chart.valueKey)}`}><title>{`${point.label}: ${chartTooltipValue(point.value, chart.valueKey)}`}</title><rect x={point.x - Math.min(28, plotWidth / points.length * .29)} y={Math.min(point.y, valueToY(0))} width={Math.min(56, plotWidth / points.length * .58)} height={Math.abs(valueToY(0) - point.y)} rx="3" className="chart-bar" /><text x={point.x} y={height - 18} textAnchor="middle" className="chart-label"><tspan className="chart-label-desktop">{truncateLabel(point.label, 22)}</tspan><tspan className="chart-label-mobile">{truncateLabel(point.label, 12)}</tspan></text></g>) : <><path d={linePath} className="chart-line" />{points.map((point) => <g key={`${point.label}-${point.x}`} aria-label={`${point.label}: ${chartTooltipValue(point.value, chart.valueKey)}`}><title>{`${point.label}: ${chartTooltipValue(point.value, chart.valueKey)}`}</title><circle cx={point.x} cy={point.y} r="4" className="chart-point" /><text x={point.x} y={height - 18} textAnchor="middle" className="chart-label"><tspan className="chart-label-desktop">{truncateLabel(point.label, 22)}</tspan><tspan className="chart-label-mobile">{truncateLabel(point.label, 12)}</tspan></text></g>)}</>}
  </svg></div>
}
