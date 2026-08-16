import { expect, test } from '@playwright/test'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

test.describe.configure({ mode: 'serial' })

const evidenceDir = resolve('test-results/evidence')
const cases = [
  {
    file: resolve('../data/202401_NFs_Cabecalho.csv'),
    name: '202401_nfs_cabecalho',
    rows: 100,
    metric: 'valor_nota_fiscal',
    total: 3371754.84,
    maximum: 1292418.75,
    questions: [
      'Quantos registros existem neste dataset?',
      'Qual é a soma total da coluna valor_nota_fiscal?',
      'Qual é o valor total das notas fiscais agrupado por uf_emitente? Retorne uma tabela ordenada.',
      'Qual é o maior valor da coluna valor_nota_fiscal e qual registro possui esse valor?',
      'Quais são os cinco municípios emitentes com maior soma de valor_nota_fiscal? Retorne uma tabela ordenada.',
    ],
  },
  {
    file: resolve('../data/202401_NFs_Itens.csv'),
    name: '202401_nfs_itens',
    rows: 565,
    metric: 'valor_total',
    total: 3371446.77,
    maximum: 985050,
    questions: [
      'Quantos registros existem neste dataset?',
      'Qual é a soma total da coluna valor_total?',
      'Quais são os cinco maiores emitentes pela soma de valor_total? Retorne uma tabela ordenada.',
      'Qual é o maior valor da coluna valor_total e qual registro possui esse valor?',
      'Qual é o valor total dos itens agrupado por uf_emitente? Retorne uma tabela ordenada.',
    ],
  },
]
const casesToRun = process.env.TWO_CSV_ONLY
  ? cases.filter((item) => item.name.endsWith(process.env.TWO_CSV_ONLY === 'items' ? 'itens' : 'cabecalho'))
  : cases

type QueryBody = { answer?: string; data?: { type?: string; value?: number; rows?: Array<Record<string, unknown>> } | null }

async function upload(page: import('@playwright/test').Page, item: (typeof cases)[number]) {
  await page.locator('input[type="file"]').setInputFiles(item.file)
  const uploadResponsePromise = page.waitForResponse((response) => response.url().endsWith('/api/datasets') && response.request().method() === 'POST')
  await page.getByRole('button', { name: /iniciar upload/i }).click()
  const response = await uploadResponsePromise
  expect(response.status()).toBe(201)
  const body = await response.json() as { datasetId: string; summary: { rows: number; columns: number } }
  expect(body.summary.rows).toBe(item.rows)
  return body.datasetId
}

async function ask(page: import('@playwright/test').Page, datasetId: string, question: string) {
  const composer = page.locator('#query-input')
  await composer.fill(question)
  const responsePromise = page.waitForResponse((response) => response.url().endsWith(`/api/datasets/${datasetId}/query`) && response.request().method() === 'POST')
  await composer.press('Enter')
  await expect(page.getByRole('status')).toContainText('Analisando dados')
  await expect(composer).toBeDisabled()
  const response = await responsePromise
  const body = await response.json() as QueryBody
  console.log('REAL_QUERY', JSON.stringify({ question, status: response.status(), body }))
  expect(response.status()).toBe(200)
  expect(body.answer).toBeTruthy()
  await expect(page.getByText('análise concluída').first()).toBeVisible({ timeout: 90000 })
  return body
}

test('real browser pipeline with both CSV files and diverse questions', async ({ page }) => {
  mkdirSync(evidenceDir, { recursive: true })
  const evidencePath = resolve(evidenceDir, 'two-csv-real-responses.json')
  const evidence: Array<{ dataset: string; question: string; response: QueryBody }> = process.env.TWO_CSV_ONLY && existsSync(evidencePath)
    ? JSON.parse(readFileSync(evidencePath, 'utf8'))
    : []
  const consoleErrors: string[] = []
  const pageErrors: string[] = []
  page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()) })
  page.on('pageerror', (error) => pageErrors.push(error.message))

  for (const [index, item] of casesToRun.entries()) {
    evidence.splice(0, evidence.length, ...evidence.filter((entry) => entry.dataset !== item.name))
    await page.goto('/')
    await expect(page.getByText('Adicione um dataset')).toBeVisible()
    const datasetId = await upload(page, item)
    await page.getByRole('button', { name: 'Explorar dados' }).click()
    await expect(page.getByRole('heading', { name: 'O que você quer descobrir?' })).toBeVisible({ timeout: 90000 })
    await expect(page.locator('.active-dataset__name')).toHaveText(item.name)
    await expect(page.locator('.sidebar-metrics dd').nth(1)).toHaveText(item.rows.toLocaleString('pt-BR'))
    await page.screenshot({ path: resolve(evidenceDir, `two-csv-${index + 1}-${item.name}-workspace.png`), fullPage: true })

    const count = await ask(page, datasetId, item.questions[0])
    expect(count.data).toEqual({ type: 'count', value: item.rows })
    const sum = await ask(page, datasetId, item.questions[1])
    expect(JSON.stringify(sum)).toContain(item.total.toFixed(2))
    const grouped = await ask(page, datasetId, item.questions[2])
    evidence.push(
      { dataset: item.name, question: item.questions[0], response: count },
      { dataset: item.name, question: item.questions[1], response: sum },
      { dataset: item.name, question: item.questions[2], response: grouped },
    )
    expect(grouped.data?.type).toBe('table')
    expect(grouped.data?.rows?.length).toBeGreaterThan(0)
    if (item.name === '202401_nfs_itens') {
      const rows = grouped.data?.rows ?? []
      expect(rows).toHaveLength(5)
      const values = rows.map((row) => Number(row.valor_total))
      expect(values).toEqual([...values].sort((left, right) => right - left))
    }
    const maximum = await ask(page, datasetId, item.questions[3])
    evidence.push({ dataset: item.name, question: item.questions[3], response: maximum })
    expect(maximum.data?.type).toBe('table')
    expect(maximum.data?.rows?.some((row) => Number(row[item.metric]) === item.maximum)).toBe(true)
    expect(Object.keys(maximum.data?.rows?.[0] ?? {}).length).toBeGreaterThan(1)

    const additionalGroup = await ask(page, datasetId, item.questions[4])
    evidence.push({ dataset: item.name, question: item.questions[4], response: additionalGroup })
    expect(additionalGroup.data?.type).toBe('table')
    const additionalRows = additionalGroup.data?.rows ?? []
    expect(additionalRows.length).toBeGreaterThan(0)
    if (item.name === '202401_nfs_cabecalho') expect(additionalRows).toHaveLength(5)
    const additionalValues = additionalRows.map((row) => Number(row[item.metric]))
    expect(additionalValues).toEqual([...additionalValues].sort((left, right) => right - left))
    writeFileSync(evidencePath, JSON.stringify(evidence, null, 2))
    await page.screenshot({ path: resolve(evidenceDir, `two-csv-${index + 1}-${item.name}-answers.png`), fullPage: true })
    expect(consoleErrors).toEqual([])
    expect(pageErrors).toEqual([])
  }
})
