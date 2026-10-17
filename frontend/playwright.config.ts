import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  timeout: 30000,
  expect: { timeout: 8000 },
  workers: 1,
  use: {
    baseURL: process.env.MARKET_TEST_URL || 'http://127.0.0.1:8871',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1440, height: 1000 } } },
    { name: 'mobile', use: { ...devices['iPhone 13'], defaultBrowserType: 'chromium' } },
  ],
  webServer: process.env.MARKET_TEST_URL
    ? undefined
    : {
        command:
          'uv run --project .. --group dev python -m uvicorn main:app --app-dir .. --host 127.0.0.1 --port 8871',
        url: 'http://127.0.0.1:8871/health',
        reuseExistingServer: false,
        timeout: 90000,
        env: {
          MARKET_API_TOKEN: 'fixture-' + 'X'.repeat(40),
          MARKET_LIVE_DATA: '0',
          MARKET_PROVIDER: '',
          MARKET_DATABASE_PATH: '../build/playwright.sqlite',
        },
      },
})
