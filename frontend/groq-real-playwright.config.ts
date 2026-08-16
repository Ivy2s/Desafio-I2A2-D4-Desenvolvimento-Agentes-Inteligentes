import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  testMatch: 'real-data-assistant.spec.ts',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 180000,
  reporter: [['list'], ['json', { outputFile: 'groq-real-e2e-results.json' }]],
  use: {
    baseURL: 'http://127.0.0.1:15176',
    browserName: 'chromium',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
  ],
  webServer: [
    {
      command: '.venv-qa/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 18002',
      cwd: '..',
      env: { ...process.env, AI_PROVIDER: 'groq', GOOGLE_API_KEY: '', CORS_ORIGINS: 'http://127.0.0.1:15176' },
      url: 'http://127.0.0.1:18002/api/health',
      reuseExistingServer: false,
      timeout: 120000,
    },
    {
      command: 'VITE_API_BASE_URL=http://127.0.0.1:18002 npm run dev -- --host 127.0.0.1 --port 15176',
      cwd: '.',
      url: 'http://127.0.0.1:15176',
      reuseExistingServer: false,
      timeout: 120000,
    },
  ],
})
