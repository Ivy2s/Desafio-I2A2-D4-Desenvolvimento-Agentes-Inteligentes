import type { ChartModel } from './deriveVisualization'
import { formatCellValue } from './tableFormatting'

export const isCurrencyMetric = (key: string) => /(^|[\s_-])(valor|preco|preço|receita|faturamento|total)([\s_-]|$)/i.test(key)

export const compactNumber = (value: number) => {
  const absolute = Math.abs(value)
  const format = (scaled: number, suffix: string) => `${scaled.toLocaleString('pt-BR', { maximumFractionDigits: absolute < 10_000_000 ? 2 : 1 })} ${suffix}`
  if (absolute >= 1_000_000_000) return format(value / 1_000_000_000, 'bi')
  if (absolute >= 1_000_000) return format(value / 1_000_000, 'mi')
  if (absolute >= 1000) return format(value / 1000, 'mil')
  return value.toLocaleString('pt-BR', { maximumFractionDigits: 2 })
}

export const chartAxisValue = (value: number, valueKey: string) => `${isCurrencyMetric(valueKey) ? 'R$ ' : ''}${compactNumber(value)}`
export const chartTooltipValue = (value: number, valueKey: string) => isCurrencyMetric(valueKey)
  ? value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2, maximumFractionDigits: 2 }).replace(/\u00a0/g, ' ')
  : formatCellValue(value)

const niceStep = (range: number, targetTicks: number) => {
  const rough = range / Math.max(targetTicks - 1, 1)
  const power = 10 ** Math.floor(Math.log10(rough || 1))
  const normalized = rough / power
  const multiplier = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 2.5 ? 2.5 : normalized <= 5 ? 5 : 10
  return multiplier * power
}

export const chartTicks = (values: number[], type: ChartModel['type'], targetTicks = 6) => {
  const dataMin = Math.min(...values)
  const dataMax = Math.max(...values)
  const min = type === 'bar' ? Math.min(0, dataMin) : dataMin
  const max = type === 'bar' ? Math.max(0, dataMax) : dataMax
  const range = max - min || Math.max(Math.abs(max), 1)
  const step = niceStep(range, targetTicks)
  const start = type === 'bar' && min >= 0 ? 0 : Math.floor(min / step) * step
  const end = Math.ceil(max / step) * step
  const ticks: number[] = []
  for (let tick = start; tick <= end + step * 0.001; tick += step) ticks.push(Number(tick.toFixed(10)))
  return ticks.length > 1 ? ticks : [start, end || step]
}
