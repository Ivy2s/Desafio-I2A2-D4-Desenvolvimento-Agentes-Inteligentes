export const formatCellValue = (value: unknown) => {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'number') return value.toLocaleString('pt-BR', { maximumFractionDigits: 6 })
  if (typeof value === 'boolean') return value ? 'Sim' : 'Não'
  return String(value)
}

export const labelForColumn = (key: string) => key.replace(/([A-Z])/g, ' $1').replace(/[_-]+/g, ' ').replace(/^./, (letter) => letter.toUpperCase())
