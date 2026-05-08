import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  retries: 0,
  fullyParallel: false,
  use: {
    baseURL: 'http://127.0.0.1:8000',
  },
  webServer: {
    command: 'python3 -m venv .venv-e2e && . .venv-e2e/bin/activate && python -m pip install -r requirements.txt && python -m uvicorn src.backend.main:app --host 127.0.0.1 --port 8000',
    url: 'http://127.0.0.1:8000/api/health',
    timeout: 120_000,
    reuseExistingServer: true,
    cwd: '..',
  },
});
