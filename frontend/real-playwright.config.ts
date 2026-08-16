import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  testMatch: 'real-data-assistant.spec.ts',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 180000,
  reporter: [['list'], ['json', { outputFile: 'real-e2e-results.json' }]],
  use: {
    baseURL: 'http://127.0.0.1:15174',
    browserName: 'chromium',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'mobile-320', use: { ...devices['Desktop Chrome'], viewport: { width: 320, height: 568 } } },
  ],
  webServer: [
    {
      command: '.venv-qa/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 18001',
      cwd: '..',
      env: { ...process.env, AI_PROVIDER: 'gemini', CORS_ORIGINS: 'http://127.0.0.1:15174' },
      url: 'http://127.0.0.1:18001/api/health',
      reuseExistingServer: false,
      timeout: 120000,
    },
    {
      command: 'VITE_API_BASE_URL=http://127.0.0.1:18001 npm run dev -- --host 127.0.0.1 --port 15174',
      cwd: '.',
      url: 'http://127.0.0.1:15174',
      reuseExistingServer: false,
      timeout: 120000,
    },
  ],
})
