import { expect, test } from '@playwright/test'
import { resolve } from 'node:path'

test('real browser upload and Gemini-to-Groq fallback', async ({ page }) => {
  const csvPath = resolve('../data/202401_NFs_Itens.csv')
  const consoleErrors: string[] = []
  const pageErrors: string[] = []
  page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()) })
  page.on('pageerror', (error) => pageErrors.push(error.message))

  await page.goto('/')
  await expect(page.getByText('Adicione um dataset')).toBeVisible()

  await page.locator('input[type="file"]').setInputFiles(csvPath)
  const uploadResponsePromise = page.waitForResponse((response) => response.url().endsWith('/api/datasets') && response.request().method() === 'POST')
  await page.getByRole('button', { name: /iniciar upload/i }).click()
  const uploadResponse = await uploadResponsePromise
  expect(uploadResponse.status()).toBe(201)
  const upload = await uploadResponse.json() as { datasetId: string; summary: { rows: number } }
  expect(upload.summary.rows).toBe(565)

  await page.getByRole('button', { name: 'Explorar dados' }).click()
  await expect(page.getByRole('heading', { name: 'O que você quer descobrir?' })).toBeVisible()

  const question = 'Quantos registros existem neste dataset?'
  const composer = page.locator('#query-input')
  await composer.fill(question)
  const queryResponsePromise = page.waitForResponse((response) => response.url().endsWith(`/api/datasets/${upload.datasetId}/query`) && response.request().method() === 'POST')
  await composer.press('Enter')
  await expect(page.getByRole('status')).toContainText('Analisando dados')
  const queryResponse = await queryResponsePromise
  const queryBody = await queryResponse.text()
  console.log('QUERY_RESPONSE_STATUS', queryResponse.status())
  console.log('QUERY_RESPONSE_BODY', queryBody)
  expect(queryResponse.status()).toBe(200)
  expect(queryResponse.request().postDataJSON()).toEqual({ question })
  const query = JSON.parse(queryBody) as { data: { type: string; value: number } }
  expect(query.data).toEqual({ type: 'count', value: 565 })
  await expect(page.getByText('análise concluída')).toBeVisible({ timeout: 90000 })
  await expect(page.getByLabel('565 registros')).toBeVisible()
  await expect(page.locator('.analysis-result')).toContainText('565')
  expect(consoleErrors).toEqual([])
  expect(pageErrors).toEqual([])
})
