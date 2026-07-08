import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const root = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": resolve(root, "src") },
    // Test files live outside this package (../tests/frontend, mirroring the
    // repo-wide /tests convention), so their bare `react` / `react-dom` /
    // Testing Library imports must be pinned to this package's copy instead
    // of walking up from the test file's directory (no node_modules there).
    dedupe: ["react", "react-dom", "@testing-library/react"],
  },
  // jsdom tests run in Vite's "web" transform mode, which serves files through
  // /@fs and enforces server.fs.allow — without the repo root allowed, any
  // test under ../tests/frontend with `@vitest-environment jsdom` fails to
  // even load ("Cannot find module /@fs/..."). Node-mode tests don't hit this.
  server: { fs: { allow: [resolve(root, "..")] } },
  test: {
    // Repo convention: unit tests live under /tests mirroring the source
    // tree — tests/frontend/<path>/test_<file> for frontend/src/<path>/<file>
    // (the Python twin lives in tests/backend/). The test_ prefix is not
    // Vitest's default glob, hence the explicit include.
    dir: resolve(root, "../tests/frontend"),
    include: ["**/test_*.{ts,tsx}"],
    // Node by default: most of the suite is pure logic and class-map
    // resolution (react-dom/server renderToStaticMarkup) with no DOM. Tests
    // that need a DOM (Testing Library) opt into jsdom per-file with a
    // `// @vitest-environment jsdom` docblock (see test_use-board-leads.tsx).
    environment: "node",
  },
});
