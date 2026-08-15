import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  retries: 0,
  timeout: 120000,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:15173',
    browserName: 'chromium',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile-320', use: { ...devices['Desktop Chrome'], viewport: { width: 320, height: 568 } } },
  ],
  webServer: [
    {
      command: 'python3 -m uvicorn api.main:app --host 127.0.0.1 --port 18000',
      cwd: '..',
      env: { ...process.env, CORS_ORIGINS: 'http://127.0.0.1:15173' },
      url: 'http://127.0.0.1:18000/api/health',
      reuseExistingServer: false,
      timeout: 120000,
    },
    {
      command: 'npm run dev -- --mode e2e --host 127.0.0.1 --port 15173',
      cwd: '.',
      env: { ...process.env, VITE_API_BASE_URL: 'http://127.0.0.1:18000' },
      url: 'http://127.0.0.1:15173',
      reuseExistingServer: false,
      timeout: 120000,
    },
  ],
})
