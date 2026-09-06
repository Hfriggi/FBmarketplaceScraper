# FBmarketplaceScraper

Busca anúncios do Facebook Marketplace por meio da API de Web Scraper da
Bright Data. O backend não abre navegador e não usa login, senha ou cookies do
Facebook.

## Configuração

Pré-requisitos: Python 3.10+ e Node.js 18+.

Informe a chave da Bright Data de uma destas formas:

- variável `BRIGHTDATA_API_KEY` no arquivo `.env` da raiz; ou
- arquivo local `backend/brightdata_api_key.txt`.

Os dois arquivos estão ignorados pelo Git. O dataset padrão é
`gd_lvt9iwuh6fbcwmx1a` e pode ser alterado por `BRIGHTDATA_DATASET_ID`.

Na raiz do projeto, execute no PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start-all.ps1
```

- Frontend: http://localhost:3000
- Backend: http://localhost:5000
- Saúde do backend: http://localhost:5000/health

## Consulta do backend

`POST /scrape` aceita, por exemplo:

```json
{
  "query": "canon",
  "baseLocation": "blumenau",
  "minPrice": 500,
  "maxPrice": 3000,
  "daysSinceListed": 3,
  "radius": 20,
  "sortBy": "newest",
  "deliveryMethod": "local_pick_up",
  "exact": false,
  "limit": 20
}
```

Valores de `baseLocation`: `indaial` ou `blumenau`.

Valores de `sortBy`: `suggested`, `newest`, `distance`, `price_asc` ou
`price_desc`.

Valores de `deliveryMethod`: `all`, `local_pick_up` ou `shipping`.

O limite máximo por consulta é 50 anúncios. A coleta da Bright Data é
assíncrona; o backend aguarda o snapshot por até 180 segundos. Esse tempo pode
ser alterado com `BRIGHTDATA_POLL_TIMEOUT_SECONDS`.

## Distância

O parâmetro `radius`, em quilômetros, é enviado ao filtro do Facebook ao redor
da cidade escolhida. Indaial usa o location ID `104032612966151` e Blumenau usa
`106081109431806`.

O Facebook pode incluir anúncios fora do raio solicitado. Como o dataset da
Bright Data retorna apenas o texto da localização, sem latitude/longitude, o
backend não afirma uma distância exata e devolve `distanciaKm: null` junto de
`distanceIsApproximate: true` nos metadados da consulta.
