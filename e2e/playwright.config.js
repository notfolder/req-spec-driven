import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  retries: 0,
  use: {
    baseURL: "http://frontend",
    trace: "retain-on-failure",
  },
  workers: 1,
});
