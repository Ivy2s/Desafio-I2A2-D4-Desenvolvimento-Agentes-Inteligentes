import { expect, test } from '@playwright/test'
import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import { dirname, resolve } from 'node:path'

const fixtureDir = resolve('e2e/fixtures')
const zipPath = resolve('e2e/fixtures/dataset.zip')

function ensureZip() {
  if (existsSync(zipPath)) return
  mkdirSync(dirname(zipPath), { recursive: true })
  execFileSync('zip', ['-j', zipPath, `${fixtureDir}/compras.csv`, `${fixtureDir}/fornecedores.csv`, `${fixtureDir}/dicionario.csv`])
}

test.beforeAll(ensureZip)

test('carrega ZIP real e disponibiliza a Interface B', async ({ page }) => {
  const requests: string[] = []
  const errors: string[] = []
  page.on('request', (request) => requests.push(`${request.method()} ${request.url()}`))
  page.on('requestfailed', (request) => errors.push(`requestfailed ${request.url()} ${request.failure()?.errorText ?? ''}`))
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()) })

  await page.goto('/')
  await expect(page.getByText('Adicione um dataset')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Data Assistent início' })).toBeVisible()

  await page.locator('input[type="file"]').setInputFiles(zipPath)
  await expect(page.getByRole('button', { name: /iniciar upload/i })).toBeVisible()
  const browserHealth = await page.evaluate(() => fetch('/api/health').then((response) => response.status))
  expect(browserHealth).toBe(200)
  await page.getByRole('button', { name: /iniciar upload/i }).click()
  await page.waitForTimeout(500)
  if (await page.getByRole('alert').isVisible()) throw new Error(`${requests.join('\n')}\n${errors.join('\n')}`)
  await page.getByRole('button', { name: 'Explorar dados' }).click()

  await expect(page.getByRole('heading', { name: 'O que você quer descobrir?' })).toBeVisible({ timeout: 120000 })
  await expect(page.locator('.sidebar-metrics dd').nth(0)).toHaveText('2')
  await expect(page.locator('.sidebar-metrics dd').nth(1)).toHaveText('7')
  await page.screenshot({ path: '../deliverables/evidence/02-dataset-ready.png', fullPage: true })
  expect(requests.some((request) => request.includes('POST http://127.0.0.1:18000/api/datasets'))).toBe(true)
  expect(errors).toEqual([])
})

test('rejeita formato inválido sem chamar a API', async ({ page }) => {
  let uploadRequests = 0
  page.on('request', (request) => { if (request.url().includes('/api/datasets')) uploadRequests += 1 })
  await page.goto('/')
  const invalidPath = resolve('e2e/fixtures/invalid.txt')
  writeFileSync(invalidPath, 'invalid')
  await page.locator('input[type="file"]').setInputFiles(invalidPath)
  await expect(page.getByRole('alert')).toContainText('formato não é aceito')
  expect(uploadRequests).toBe(0)
})

test('consulta real usa o endpoint do agente quando a IA está configurada', async ({ page }) => {
  await page.goto('/')
  const health = await page.request.get('http://127.0.0.1:18000/api/health')
  test.skip(!(await health.json()).aiConfigured, 'REAL_GEMINI_E2E = NOT_RUN_NO_CREDENTIAL')
  await page.locator('input[type="file"]').setInputFiles(zipPath)
  await page.getByRole('button', { name: /iniciar upload/i }).click()
  await page.getByRole('button', { name: 'Explorar dados' }).click()
  await expect(page.getByRole('heading', { name: 'O que você quer descobrir?' })).toBeVisible({ timeout: 120000 })
  const queryRequest = page.waitForRequest((request) => request.url().includes('/api/datasets/') && request.url().endsWith('/query'))
  await page.locator('#query-input').fill('Quantos registros existem?')
  await page.locator('#query-input').press('Enter')
  await queryRequest
  await expect(page.getByText('análise concluída')).toHaveCount(1, { timeout: 120000 })
  await expect(page.locator('.result-answer')).toContainText(/[34]/)
  await page.screenshot({ path: '../deliverables/evidence/03-query-real.png', fullPage: true })
})

async function openRealWorkspace(page: import('@playwright/test').Page) {
  await page.goto('/')
  const health = await page.request.get('http://127.0.0.1:18000/api/health')
  test.skip(!(await health.json()).aiConfigured, 'REAL_AGENT_E2E = NOT_RUN_NO_CREDENTIAL')
  await page.locator('input[type="file"]').setInputFiles(zipPath)
  await page.getByRole('button', { name: /iniciar upload/i }).click()
  await page.getByRole('button', { name: 'Explorar dados' }).click()
  await expect(page.getByRole('heading', { name: 'O que você quer descobrir?' })).toBeVisible({ timeout: 120000 })
}

async function askRealQuestion(page: import('@playwright/test').Page, question: string) {
  const queryRequest = page.waitForRequest((request) => request.url().includes('/api/datasets/') && request.url().endsWith('/query'))
  await page.locator('#query-input').fill(question)
  await page.locator('#query-input').press('Enter')
  await queryRequest
  await expect(page.getByText('análise concluída')).toHaveCount(1, { timeout: 60000 })
  return page.locator('.analysis-result').first()
}

test('resposta real de contagem', async ({ page }) => {
  await openRealWorkspace(page)
  const countResult = await askRealQuestion(page, 'Quantos registros existem no dataset compras?')
  await expect(countResult).toContainText('4')
  await page.screenshot({ path: '../deliverables/evidence/03-query-count.png', fullPage: true })
})

test('resposta real em tabela e gráfico', async ({ page }) => {
  await openRealWorkspace(page)
  const totalsResult = await askRealQuestion(page, 'Para o dataset compras, calcule a soma da coluna valor agrupada pela coluna fornecedor.')
  await expect(totalsResult).toContainText(/3[.\s]500/)
  await expect(totalsResult).toContainText('Alfa')
  await expect(totalsResult.locator('table')).toBeVisible()
  await expect(totalsResult.locator('svg[role="img"]')).toBeVisible()
  await page.screenshot({ path: '../deliverables/evidence/04-query-table-chart.png', fullPage: true })
})

test('resposta real em lista tabular', async ({ page }) => {
  await openRealWorkspace(page)
  const listResult = await askRealQuestion(page, 'Liste as linhas do dataset compras ordenadas pela coluna valor.')
  await expect(listResult.locator('table')).toBeVisible()
  await expect(listResult).toContainText(/(?:2[.\s]500|2500)/)
  await expect(listResult).toContainText('Monitor')
  await page.screenshot({ path: '../deliverables/evidence/05-query-list.png', fullPage: true })
})

test('quarta resposta real em dataset secundário', async ({ page }) => {
  await openRealWorkspace(page)
  const secondaryResult = await askRealQuestion(page, 'Quantos registros existem no dataset fornecedores?')
  await expect(secondaryResult).toContainText('3')
  await page.screenshot({ path: '../deliverables/evidence/06-query-maximum.png', fullPage: true })
})
