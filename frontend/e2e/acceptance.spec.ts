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
  await expect(page.locator('.result-answer')).toContainText('4')
  await expect(page.locator('.result-answer')).toContainText('3')
  await page.screenshot({ path: '../deliverables/evidence/03-query-real.png', fullPage: true })
})
