import { describe, expect, it } from 'vitest'
import { formatCellValue, labelForColumn } from './tableFormatting'

describe('DataTable presentation helpers', () => {
  it('preserves valid zero and false values', () => {
    expect(formatCellValue(0)).toBe('0')
    expect(formatCellValue(false)).toBe('Não')
  })

  it('renders missing and empty values as a visual placeholder', () => {
    expect(formatCellValue(null)).toBe('—')
    expect(formatCellValue('')).toBe('—')
  })

  it('humanizes labels without changing source keys', () => {
    expect(labelForColumn('valor_total')).toBe('Valor total')
    expect(labelForColumn('codigoFornecedor')).toBe('Codigo Fornecedor')
  })
})
