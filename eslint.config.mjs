import js from "@eslint/js";

export default [
  {
    ignores: ["node_modules/**"],
  },
  js.configs.recommended,
  {
    files: ["static/js/**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "script",
      globals: {
        window: "readonly",
        document: "readonly",
        navigator: "readonly",
        location: "readonly",
        localStorage: "readonly",
        sessionStorage: "readonly",
        fetch: "readonly",
        FormData: "readonly",
        URL: "readonly",
        URLSearchParams: "readonly",
        EventSource: "readonly",
        Blob: "readonly",
        File: "readonly",
        Audio: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly",
        console: "readonly",
      },
    },
    rules: {
      "no-unused-vars": ["warn", { args: "none" }],
      "no-console": "off",
    },
  },
];
