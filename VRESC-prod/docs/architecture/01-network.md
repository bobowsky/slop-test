# Network Architecture

## Overview

VRESC runs as two processes in development: a **Flask backend** and an optional **Vite dev server**. In production only Flask is needed.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Browser                                                            │
│                                                                     │
│  GET /api/scene  ──────────────────────────────────────────►  JSON  │
│  GET /content/*  ──────────────────────────────────────────►  media │
│  import() /content/gadgets/*.js   ─────────────────────────►  JS    │
│  import() /content/rooms/*/hotspots/*/interface.js  ───────►  JS    │
│  <script src="https://aframe.io/..."> ─────────────────────►  CDN   │
└─────────────────────────────────────────────────────────────────────┘
         │                                        │
         │ (dev: via Vite proxy)                  │ (always direct to CDN)
         ▼                                        ▼
┌──────────────────┐                  ┌───────────────────────────┐
│  Vite :5173      │                  │  aframe.io CDN            │
│  HTTPS           │                  │  A-Frame 1.5.0            │
│  @vitejs/plugin- │                  └───────────────────────────┘
│  basic-ssl       │
│                  │
│  Proxy rules:    │
│  /api    ──────► │─────────┐
│  /static ──────► │─────────┤
│  /resource ────► │─────────┤
└──────────────────┘         │
                             ▼
                  ┌──────────────────────┐
                  │  Flask :5000         │
                  │  HTTP  (debug=True)  │
                  │                     │
                  │  GET /              │
                  │  GET /api/scene     │
                  │  GET /content/<path>│
                  └──────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  content/            │
                  │  (filesystem)        │
                  │                     │
                  │  rooms/<id>/        │
                  │  gadgets/           │
                  └──────────────────────┘
```

## Processes and Ports

| Process | Port | Protocol | Purpose |
|---------|------|----------|---------|
| Flask (`app.py`) | **5000** | HTTP | API + static content serving |
| Vite (`npm run dev`) | **5173** | HTTPS (self-signed) | Dev server with hot-reload; required for WebXR |

## Why Two Processes?

WebXR (VR mode) requires a **secure context** (`https://`). Flask runs plain HTTP, so in development Vite wraps it with a self-signed TLS certificate via `@vitejs/plugin-basic-ssl`. In production, use a reverse proxy (nginx, caddy) for TLS termination in front of Flask.

## Vite Proxy Rules

Vite forwards these prefixes to Flask at `http://127.0.0.1:5000`:

| Prefix | Proxied |
|--------|---------|
| `/api` | Yes |
| `/static` | Yes |
| `/resource` | Yes |
| `/content` | **No** — not in `vite.config.js` |

> **Note:** `/content` is not proxied by Vite. Requests for media files and gadget ES modules (which all use `/content/…` paths) go directly to Flask on port 5000 from the browser, bypassing Vite. This works in practice because Flask is reachable on `:5000` directly, but it means those requests are not HTTPS when accessed via the Vite port. For full HTTPS coverage in dev, add `/content` to the Vite proxy config.

## Communication Pattern

| Caller | Target | Mechanism |
|--------|--------|-----------|
| Browser JS (`app.js`) | Flask `/api/scene` | `fetch()` — one request at startup |
| Browser (A-Frame) | Flask `/content/rooms/…` | `<video src>`, `<img src>` — media assets |
| Browser (ES module loader) | Flask `/content/gadgets/…` | `import()` — gadget modules |
| Browser (ES module loader) | Flask `/content/rooms/…/hotspots/…/interface.js` | Dynamic `import()` on hotspot click |

There are **no WebSockets** in this application. All communication is HTTP request/response or static asset loading.

## External Dependencies

| Dependency | URL | Version | Used for |
|------------|-----|---------|---------|
| A-Frame | `https://aframe.io/releases/1.5.0/aframe.min.js` | 1.5.0 | VR scene rendering, WebXR |

A-Frame is loaded from CDN in `templates/index.html`. It is not bundled or vendored.

## Mermaid Diagram

See [`diagrams/network.mmd`](diagrams/network.mmd).
