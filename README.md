# FBmarketplaceScraper

## Execução local

Pré-requisitos: Python 3.10+ e Node.js 18+.

Na raiz do projeto, execute no PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start-all.ps1
```

O script cria `backend\venv`, instala as dependências Python, instala os pacotes do React e inicia:

- Frontend: http://localhost:3000
- Backend: http://localhost:5000

Para login automático no Facebook, configure `FB_EMAIL` e `FB_PASSWORD` em um arquivo `.env` na raiz do projeto. O Selenium também pode reutilizar `backend\facebook_cookies.json`.