import { defineConfig } from "vite";

export default defineConfig({
  build: {
    outDir: "dist",
    target: "esnext",
  },
  server: {
    headers: {
      "Cross-Origin-Opener-Policy": "same-origin",
      "Cross-Origin-Embedder-Policy": "credentialless",
    },
  },
});
