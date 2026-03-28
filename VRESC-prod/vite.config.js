import { defineConfig } from "vite";
import basicSsl from "@vitejs/plugin-basic-ssl";

export default defineConfig({
  plugins: [basicSsl()],
  root: ".",
  server: {
    host: "0.0.0.0",
    port: 5173,
    https: true,
    proxy: {
      "/api":      "http://127.0.0.1:5000",
      "/resource": "http://127.0.0.1:5000",
      "/static":   "http://127.0.0.1:5000",
    },
  },
});
