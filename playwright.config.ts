import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: 'http://127.0.0.1:8110',
    viewport: { width: 1440, height: 1100 },
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'uv run uvicorn catalogmesh.main:app --host 127.0.0.1 --port 8110',
    url: 'http://127.0.0.1:8110/api/health',
    reuseExistingServer: false,
    env: { CATALOGMESH_DB: `data/e2e-${Date.now()}.db`, CATALOGMESH_ENABLE_LIVE: 'false' },
  },
})
