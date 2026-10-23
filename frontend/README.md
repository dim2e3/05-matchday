# MatchDay frontend

React 19 + TypeScript + Vite, plain CSS. Tabs: My Games, Teams, Notifications; Connect
Telegram in the header. Overview: [root README](../README.md).

```sh
npm ci
npm run dev        # http://localhost:5173, proxies /api to the backend on :8001
npm test           # Vitest + React Testing Library
npm run lint       # oxlint
npm run build      # typecheck + production build (served by nginx in Docker)
```
