# Doctor Dashboard

React 18 + TypeScript dashboard for the synthetic HappyHealth virtual patient.
The browser calls Spring Boot only; it never calls the model or MQTT broker directly.

```powershell
npm install
npm run dev
```

Vite proxies `/api` to `http://127.0.0.1:8080`. Set `VITE_API_BASE_URL` only when
the backend is available at a different browser-reachable URL. Never put secrets in
Vite environment variables because browser users can read them.

Verification:

```powershell
npm test
npm run build
```
