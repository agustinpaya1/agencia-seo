// @ts-check
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

/**
 * Plain ESM (.mjs) on purpose — do not convert back to next.config.ts: under
 * Node 26, Next 16.2.9 compiles the .ts config to CJS but loads it as ESM
 * ("exports is not defined in ES module scope"), which is fatal for
 * `next build` and silently drops the config (no cacheComponents) in dev.
 *
 * @type {import("next").NextConfig}
 */
const nextConfig = {
  cacheComponents: true,

  // The root package-lock.json exists for the Lighthouse CLI used by
  // backend/app/audit_engine/performance.py (subprocess).  Pointing
  // outputFileTracingRoot at the monorepo root tells Next.js about it so it
  // stops emitting the "lockfile in parent directory" warning.
  outputFileTracingRoot: resolve(__dirname, ".."),
};

export default nextConfig;
