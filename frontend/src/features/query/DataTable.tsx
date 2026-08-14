interface DataTableProps { columns: string[]; rows: Record<string, unknown>[] }

const formatValue = (value: unknown, column: string) => {
  if (typeof value !== 'number') return String(value ?? '—')
  if (column === 'valor' || column === 'total') return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
  return value.toLocaleString('pt-BR', { maximumFractionDigits: 2 })
}
const labelFor = (key: string) => key.replace(/([A-Z])/g, ' $1').replace(/^./, (letter) => letter.toUpperCase())

export function DataTable({ columns, rows }: DataTableProps) {
  return <div className="table-scroll"><table><thead><tr>{columns.map((column) => <th key={column}>{labelFor(column)}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{columns.map((column) => <td key={column} className={typeof row[column] === 'number' ? 'numeric' : ''}>{formatValue(row[column], column)}</td>)}</tr>)}</tbody></table></div>
}
