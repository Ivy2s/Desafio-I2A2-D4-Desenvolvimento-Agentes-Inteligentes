import { describe, expect, it } from 'vitest'
import type { TableData } from '../../contracts/dataAssistant'
import { deriveVisualization, MAX_CHART_CATEGORIES } from './deriveVisualization'

const table = (columns: string[], rows: Record<string, unknown>[]): TableData => ({
  type: 'table', columns, rows, truncated: false, returnedRows: rows.length,
})

describe('deriveVisualization', () => {
  it('derives a bar chart from one category and one numeric column', () => {
    const result = deriveVisualization(table(['categoria', 'valor'], [{ categoria: 'B', valor: 10 }, { categoria: 'A', valor: 20 }]))
    expect(result).toMatchObject({ type: 'bar', categoryKey: 'categoria', valueKey: 'valor' })
    expect(result?.rows.map((row) => row.categoria)).toEqual(['B', 'A'])
  })

  it('derives a line chart only for a clearly temporal category', () => {
    const result = deriveVisualization(table(['mes', 'total'], [{ mes: 'Jan', total: 10 }, { mes: 'Fev', total: 20 }]))
    expect(result?.type).toBe('line')
  })

  it('does not derive a chart without a numeric measure', () => {
    expect(deriveVisualization(table(['nome', 'cidade'], [{ nome: 'A', cidade: 'SP' }]))).toBeNull()
  })

  it('does not choose arbitrarily between multiple measures', () => {
    expect(deriveVisualization(table(['produto', 'quantidade', 'valor'], [{ produto: 'A', quantidade: 1, valor: 2 }]))).toBeNull()
  })

  it('handles empty, null and overly large results safely', () => {
    expect(deriveVisualization(table(['categoria', 'valor'], []))).toBeNull()
    expect(deriveVisualization(table(['categoria', 'valor'], [{ categoria: 'A', valor: null }]))).toBeNull()
    const rows = Array.from({ length: MAX_CHART_CATEGORIES + 1 }, (_, index) => ({ categoria: String(index), valor: index }))
    expect(deriveVisualization(table(['categoria', 'valor'], rows))).toBeNull()
  })
})
