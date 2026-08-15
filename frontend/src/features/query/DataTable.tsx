import type { TableData } from '../../contracts/dataAssistant'
import { formatCellValue, labelForColumn } from './tableFormatting'
interface DataTableProps { table: TableData }

export function DataTable({ table }: DataTableProps) {
  const { columns, rows } = table
  if (rows.length === 0) return <p className="table-empty">Nenhum registro retornado.</p>
  return <div className="table-scroll"><table><thead><tr>{columns.map((column) => <th key={column} scope="col">{labelForColumn(column)}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{columns.map((column) => <td key={column} className={typeof row[column] === 'number' ? 'numeric' : ''}>{formatCellValue(row[column])}</td>)}</tr>)}</tbody></table></div>
}
