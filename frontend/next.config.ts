import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { NextConfig } from "next";

const __dirname = dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  cacheComponents: true,

  // The root package-lock.json exists for the Lighthouse CLI used by
  // backend/app/audit_engine/performance.py (subprocess).  Pointing
  // outputFileTracingRoot at the monorepo root tells Next.js about it so it
  // stops emitting the "lockfile in parent directory" warning.
  outputFileTracingRoot: resolve(__dirname, ".."),
};

export default nextConfig;
