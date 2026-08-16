import type { TableData } from '../../contracts/dataAssistant'

export const MAX_CHART_CATEGORIES = 20

export type ChartModel = {
  type: 'bar' | 'line'
  categoryKey: string
  valueKey: string
  rows: Record<string, unknown>[]
}

const isNumericColumn = (table: TableData, column: string) => {
  const values = table.rows.map((row) => row[column]).filter((value) => value !== null && value !== undefined)
  return values.length > 0 && values.every((value) => typeof value === 'number' && Number.isFinite(value))
}

const isTemporalKey = (key: string) => /(^|_)(data|date|mes|mês|month|ano|year)($|_)/i.test(key)

export function deriveVisualization(table: TableData): ChartModel | null {
  if (table.rows.length < 2 || table.rows.length > MAX_CHART_CATEGORIES) return null

  const numericColumns = table.columns.filter((column) => isNumericColumn(table, column))
  if (numericColumns.length !== 1) return null

  const valueKey = numericColumns[0]
  const categoryColumns = table.columns.filter((column) => column !== valueKey && table.rows.every((row) => {
    const value = row[column]
    return value !== null && value !== undefined && (typeof value === 'string' || typeof value === 'number')
  }))
  if (categoryColumns.length !== 1) return null

  const categoryKey = categoryColumns[0]
  const categories = new Set(table.rows.map((row) => row[categoryKey]))
  if (categories.size > MAX_CHART_CATEGORIES) return null

  return { type: isTemporalKey(categoryKey) ? 'line' : 'bar', categoryKey, valueKey, rows: table.rows }
}
