import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  testMatch: 'two-csv-real.spec.ts',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 180000,
  reporter: [['list'], ['json', { outputFile: 'two-csv-real-results.json' }]],
  use: {
    baseURL: 'http://127.0.0.1:15178',
    browserName: 'chromium',
    viewport: { width: 1440, height: 900 },
    ...devices['Desktop Chrome'],
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
  webServer: [
    {
      command: '.venv-qa/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 18004',
      cwd: '..',
      env: { ...process.env, AI_PROVIDER: 'gemini', CORS_ORIGINS: 'http://127.0.0.1:15178' },
      url: 'http://127.0.0.1:18004/api/health',
      reuseExistingServer: false,
      timeout: 120000,
    },
    {
      command: 'VITE_API_BASE_URL=http://127.0.0.1:18004 npm run dev -- --host 127.0.0.1 --port 15178',
      cwd: '.',
      url: 'http://127.0.0.1:15178',
      reuseExistingServer: false,
      timeout: 120000,
    },
  ],
})
