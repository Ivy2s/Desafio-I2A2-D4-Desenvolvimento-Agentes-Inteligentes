import { expect, test, type Page } from '@playwright/test'
import { mkdirSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'

test.describe.configure({ mode: 'serial' })

const csvPath = resolve('../data/202401_NFs_Itens.csv')
const evidenceDir = resolve('test-results/evidence')
const expected = JSON.parse(readFileSync(resolve('e2e/fixtures/real-e2e-expected-results.json'), 'utf8')) as {
  rows: number
  column_count: number
  columns: string[]
  sum_valor_total: number
  max_valor_total: number
  min_valor_total: number
  average_valor_total: number
  top5_emitentes_sum: Array<{ group: string; value: number }>
  sum_by_uf_emitente: Array<{ group: string; value: number }>
  max_by_emitente: Array<{ group: string; value: number }>
  min_by_emitente: Array<{ group: string; value: number }>
  average_by_uf_emitente: Array<{ group: string; value: number }>
}

const questions = [
  'Quantos registros existem neste dataset?',
  'Qual é o maior valor da coluna valor_total e qual registro possui esse valor?',
  'No dataset 202401_nfs_itens, agrupe por razao_social_emitente, calcule a soma de valor_total, ordene por valor_total e retorne os 5 primeiros resultados.',
  'No dataset 202401_nfs_itens, agrupe por uf_emitente, calcule a soma de valor_total e ordene por valor_total.',
  'No dataset 202401_nfs_itens, agrupe por uf_emitente, calcule a soma de valor_total e informe também o total geral.',
  'No dataset 202401_nfs_itens, agrupe por uf_emitente, calcule o min de valor_total e retorne os resultados.',
  'No dataset 202401_nfs_itens, agrupe por uf_emitente, calcule a média de valor_total e ordene por valor_total.',
  'No dataset 202401_nfs_itens, liste 20 registros com as colunas descricao_do_produto_servico e valor_total.',
]

type NetworkRecord = { id: number; status: number; durationMs: number; datasetId: string; body: unknown }

function addBrowserDiagnostics(page: Page) {
  const consoleErrors: string[] = []
  const pageErrors: string[] = []
  const failedRequests: string[] = []
  page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()) })
  page.on('pageerror', (error) => pageErrors.push(error.message))
  page.on('requestfailed', (request) => failedRequests.push(`${request.method()} ${request.url()} ${request.failure()?.errorText ?? ''}`))
  return { consoleErrors, pageErrors, failedRequests }
}

async function uploadCsv(page: Page) {
  await page.locator('input[type="file"]').setInputFiles(csvPath)
  await expect(page.getByRole('button', { name: /iniciar upload/i })).toBeVisible()
  const responsePromise = page.waitForResponse((response) => response.url().endsWith('/api/datasets') && response.request().method() === 'POST')
  await page.getByRole('button', { name: /iniciar upload/i }).click()
  const response = await responsePromise
  expect(response.status()).toBe(201)
  const payload = await response.json() as { datasetId: string; status: string; summary: { files: number; rows: number; columns: number }; datasets: Array<{ name: string }> }
  expect(payload.datasetId).toMatch(/^[0-9a-f-]{36}$/i)
  expect(payload.status).toBe('ready')
  expect(payload.summary).toMatchObject({ files: 1, rows: expected.rows, columns: expected.column_count })
  expect(payload.datasets).toHaveLength(1)
  return payload.datasetId
}

async function ask(page: Page, datasetId: string, question: string, id: number, records: NetworkRecord[]) {
  const composer = page.locator('#query-input')
  await composer.fill(question)
  const started = Date.now()
  const responsePromise = page.waitForResponse((response) => response.url().endsWith(`/api/datasets/${datasetId}/query`) && response.request().method() === 'POST')
  await composer.press('Enter')
  await expect(page.getByRole('status')).toContainText('Analisando dados')
  await expect(composer).toBeDisabled()
  const response = await responsePromise
  const durationMs = Date.now() - started
  const requestBody = response.request().postDataJSON()
  expect(requestBody).toEqual({ question })
  expect(response.status()).toBe(200)
  const body = await response.json() as { answer: string; data: { type: string; value?: number; columns?: string[]; rows?: Array<Record<string, unknown>> } | null }
  if (JSON.stringify(body).includes('429') || JSON.stringify(body).includes('ResourceExhausted')) test.fail(true, 'E2E_INTERRUPTED_BY_EXTERNAL_QUOTA')
  await expect(page.getByText('análise concluída').first()).toBeVisible({ timeout: 90000 })
  records.push({ id, status: response.status(), durationMs, datasetId, body: requestBody })
  await page.screenshot({ path: resolve(evidenceDir, `0${id + 2}-question-${String(id).padStart(2, '0')}.png`), fullPage: true })
  return body
}

test('real browser data assistant: CSV, Gemini, tools, workspace and eight queries', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium', 'the eight-query battery runs once on desktop')
  mkdirSync(evidenceDir, { recursive: true })
  const diagnostics = addBrowserDiagnostics(page)
  const records: NetworkRecord[] = []
  await page.goto('/')
  await expect(page.getByRole('link', { name: 'Data Assistent início' })).toBeVisible()
  await expect(page.getByText('Adicione um dataset')).toBeVisible()
  await expect(page.getByRole('region', { name: 'Área para envio do dataset' })).toBeVisible()
  await page.screenshot({ path: resolve(evidenceDir, '01-initial-state.png'), fullPage: true })

  const datasetId = await uploadCsv(page)
  await page.screenshot({ path: resolve(evidenceDir, '02-real-csv-loaded.png'), fullPage: true })
  await page.getByRole('button', { name: 'Explorar dados' }).click()
  await expect(page.getByRole('heading', { name: 'O que você quer descobrir?' })).toBeVisible({ timeout: 90000 })
  await expect(page.locator('.active-dataset__name')).toHaveText('202401_nfs_itens')
  await expect(page.locator('.sidebar-metrics dd').nth(0)).toHaveText('1')
  await expect(page.locator('.sidebar-metrics dd').nth(1)).toHaveText(expected.rows.toLocaleString('pt-BR'))
  await expect(page.locator('.sidebar-metrics dd').nth(2)).toHaveText(String(expected.column_count))
  await expect(page.locator('.sidebar-files')).toContainText('202401_nfs_itens')

  const q1 = await ask(page, datasetId, questions[0], 1, records)
  expect(q1.data).toEqual({ type: 'count', value: expected.rows })

  const q2 = await ask(page, datasetId, questions[1], 2, records)
  expect(q2.data?.type).toBe('table')
  expect((q2.data as { rows: Array<Record<string, unknown>> }).rows.some((row) => Number(row.valor_total) === expected.max_valor_total)).toBe(true)

  const q3 = await ask(page, datasetId, questions[2], 3, records)
  expect(q3.data?.type).toBe('table')
  expect((q3.data as { rows: Array<Record<string, unknown>> }).rows.slice(0, 5).map((row) => ({ group: row.razao_social_emitente, value: row.valor_total }))).toEqual(expected.top5_emitentes_sum.map((row) => ({ group: row.group, value: row.value })))
  await expect(page.locator('.analysis-result').first().locator('table')).toBeVisible()
  await expect(page.locator('.analysis-result').first().locator('svg[role="img"]')).toBeVisible()
  await page.screenshot({ path: resolve(evidenceDir, '05-top5-table-chart.png'), fullPage: true })

  const q4 = await ask(page, datasetId, questions[3], 4, records)
  expect(q4.data?.type).toBe('table')
  const q4Rows = (q4.data as { rows: Array<Record<string, unknown>> }).rows
  expect(q4Rows.map((row) => ({ group: row.uf_emitente, value: row.valor_total }))).toEqual(expected.sum_by_uf_emitente.map((row) => ({ group: row.group, value: row.value })))

  const q5 = await ask(page, datasetId, questions[4], 5, records)
  expect(q5.data?.type).toBe('table')
  const q5Rows = (q5.data as { rows: Array<Record<string, unknown>> }).rows
  expect(q5Rows.reduce((sum, row) => sum + Number(row.valor_total), 0)).toBeCloseTo(expected.sum_valor_total, 2)

  const q6 = await ask(page, datasetId, questions[5], 6, records)
  expect(q6.data?.type).toBe('table')
  expect((q6.data as { rows: Array<Record<string, unknown>> }).rows.some((row) => Number(row.valor_total) === expected.min_valor_total)).toBe(true)

  const q7 = await ask(page, datasetId, questions[6], 7, records)
  expect(q7.data?.type).toBe('table')
  const q7Rows = (q7.data as { rows: Array<Record<string, unknown>> }).rows
  expect(q7Rows.map((row) => ({ group: row.uf_emitente, value: row.valor_total }))).toEqual(expected.average_by_uf_emitente.map((row) => ({ group: row.group, value: row.value })))

  const q8 = await ask(page, datasetId, questions[7], 8, records)
  expect(q8.data?.type).toBe('table')
  await expect(page.locator('.analysis-result')).toHaveCount(8)
  await expect(page.getByText('8 consultas')).toBeVisible()
  await page.screenshot({ path: resolve(evidenceDir, '06-final-history.png'), fullPage: true })
  expect(records).toHaveLength(8)
  expect(new Set(records.map((record) => record.datasetId))).toEqual(new Set([datasetId]))
  expect(diagnostics.consoleErrors).toEqual([])
  expect(diagnostics.pageErrors).toEqual([])
  expect(diagnostics.failedRequests).toEqual([])
})

test('real browser mobile: same CSV, workspace, query and no horizontal overflow', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile-320', 'mobile evidence runs only in the mobile project')
  const diagnostics = addBrowserDiagnostics(page)
  await page.goto('/')
  const datasetId = await uploadCsv(page)
  await page.getByRole('button', { name: 'Explorar dados' }).click()
  await expect(page.getByRole('heading', { name: 'O que você quer descobrir?' })).toBeVisible({ timeout: 90000 })
  const body = await ask(page, datasetId, questions[0], 1, [])
  expect(body.data).toEqual({ type: 'count', value: expected.rows })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  await page.screenshot({ path: resolve(evidenceDir, '07-mobile.png'), fullPage: true })
  expect(diagnostics.consoleErrors).toEqual([])
  expect(diagnostics.pageErrors).toEqual([])
  expect(diagnostics.failedRequests).toEqual([])
})
