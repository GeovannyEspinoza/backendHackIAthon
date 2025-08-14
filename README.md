# Backend — Scoring Alternativo para PYMEs (Scraping + Finanzas + LLM)

Plataforma backend (FastAPI) que orquesta:

* **Ingesta financiera** (SuperCías u origen del frontend).
* **Scraping no tradicional**: TikTok y Google Maps (opiniones, engagement).
* **Análisis**: features de reputación/sentimiento y fusión en un **puntaje 0–100** con etiqueta de riesgo y crédito sugerido.
* **API REST** para el frontend (dashboard).

> **Nota de demo**: el endpoint principal permite ejecutar con **scrapers apagados** (`run_scrapers=false`) y/o **modo mock** (`mock=true`), útil para despliegues sin navegador (p.ej. Heroku).

---

## 🔧 Stack

* Python 3.12, FastAPI, Uvicorn
* Playwright (Chromium) para scraping
* Pandas, VADER (sentiment), langdetect
* Diseño de fusión simple (finanzas + redes)

---

## 📁 Estructura

```
backend/
├─ app/
│  ├─ main.py              # FastAPI (rutas /api/*)
│  ├─ models.py            # Esquemas Pydantic
│  ├─ pipeline.py          # Orquestación de scraping/análisis/fusión
│  ├─ llm_finance.py       # (opcional) lógica LLM de score financiero
│  ├─ config.py            # Config/env helpers
│  ├─ logging_conf.py      # Logger
│  ├─ services/
│  │  ├─ pipeline.py       # (si lo estás usando, mantener import estable)
│  │  ├─ captcha_utils.py  # utilidades AntiCaptcha + Playwright
│  │  ├─ solver_anticaptcha.py
│  │  └─ supercias/        # scripts auxiliares de SuperCías
│  ├─ scrapers/
│  │  ├─ tiktok_scraper.py
│  │  └─ gmaps_scraper_noapi.py
│  └─ analysis/
│     ├─ analyze_tiktok.py
│     └─ analyze_maps.py
├─ requirements.txt
├─ .env.example
└─ README.md
```

> Si corres el scraper de TikTok en *modo bootstrap*, se creará `tiktok_profile/` y `tiktok_state.json` para persistir cookies.

---

## 🚀 Arranque local

Desde el directorio `backend/`:

```bash
# 1) Opcional: crear venv
python -m venv .venv && source .venv/bin/activate

# 2) Instalar dependencias
pip install -r requirements.txt

# 3) Instalar navegadores de Playwright (si vas a scrapear)
python -m playwright install chromium

# 4) Exportar PYTHONPATH para imports absolutos (app.*)
export PYTHONPATH=$(pwd)

# 5) Levantar API
uvicorn app.main:app --reload --port 8000
```

* Salud:

  * `GET http://127.0.0.1:8000/healthz`
  * `GET http://127.0.0.1:8000/api/healthz`
* Docs Swagger: `http://127.0.0.1:8000/docs`

---

## 🔑 Variables de entorno

Crea un `.env` (o usa variables del sistema):

```
# Scraping (opcional)
ANTICAPTCHA_API_KEY=your_key   # si usas solver automático

# FastAPI / entorno
ENV=dev
```

> Sin `ANTICAPTCHA_API_KEY` puedes usar `interactive=true` (resolver CAPTCHA manual) o `run_scrapers=false`/`mock=true`.

---

## 🧠 API

### Salud

```
GET /api/healthz
→ 200 {"ok": true}
```

### Orquestación

```
POST /api/orchestrate
```

**Body (JSON):**

```json
{
  "ruc": "1790015474001",
  "tiktok": "nike",
  "gmaps": "Nike Miraflores",
  "run_scrapers": false,
  "mock": true,
  "use_solver": true,
  "headless": true,
  "video_limit": 10,
  "comments_per_video": 5,
  "comment_pages": 3,
  "weights": { "fin": 0.60, "maps": 0.25, "tt": 0.15 }
}
```

**Parámetros clave**

* `run_scrapers`: `true` para ejecutar Playwright (si tu hosting lo permite).
* `mock`: `true` devuelve scores demo sin scraping.
* `use_solver`: usa AntiCaptcha si hay desafíos.
* `weights`: ponderación de componentes (finanzas / maps / tiktok).

**Respuesta (ejemplo con mock):**

```json
{
  "ruc": "1790015474001",
  "used_files": { "gmaps": null, "tiktok": null },
  "component_scores": { "fin": 0.6, "maps": null, "tt": null },
  "final_score": 0.6,
  "risk_label": "medio"
}
```

---

## 🕷️ Scraping (opcional)

### TikTok

1. **Bootstrap (una sola vez)** para guardar cookies:

```bash
python app/scrapers/tiktok_scraper.py --bootstrap --username nike
# deja la ventana, resuelve retos si aparecen y presiona Enter en la terminal
```

2. **Scrape**:

```bash
python app/scrapers/tiktok_scraper.py --username nike \
  --top-k 5 --video-limit 10 --comments-per-video 5 --comment-pages 3 \
  --headless true --interactive false --use-solver true
```

Genera:

* `nike_videos.json/.csv`
* `nike_comments.json/.csv`
* `nike_features.json` (si corres el análisis)

### Google Maps

```bash
python app/scrapers/gmaps_scraper_noapi.py --company "Nike Miraflores" \
  --max-reviews 120 --headless true --interactive false --use-solver true
```

Genera:

* `nike-miraflores_maps_meta.json`
* `nike-miraflores_maps_reviews.json/.csv`

---

## 📊 Análisis offline (features)

```bash
# TikTok → features
python app/analysis/analyze_tiktok.py --username nike

# Google Maps → features
python app/analysis/analyze_maps.py --company "Nike Miraflores"
```

Salidas:

* `*_features.json` con métricas agregadas y puntaje de riesgo de reputación.

---

## 🧩 Fusión de puntajes

El `pipeline` combina:

* **Finanzas** (p.ej., score base de 0–1 desde métricas/LLM).
* **Maps/TikTok** (sentiment, quejas, n-grams, engagement, recencia).
* **Pesos** configurables → `final_score` (0–1) y `risk_label` (`bajo`/`medio`/`alto`).

---

## 🧪 Ejemplos curl

**Mock** (sin scraping):

```bash
curl -X POST http://127.0.0.1:8000/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "ruc":"1790015474001",
    "tiktok":"nike",
    "gmaps":"Nike Miraflores",
    "run_scrapers": false,
    "mock": true
  }'
```

**Con scraping** (requiere Playwright y, si hay retos, solver o modo interactivo):

```bash
curl -X POST http://127.0.0.1:8000/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "ruc":"1790015474001",
    "tiktok":"nike",
    "gmaps":"Nike Miraflores",
    "run_scrapers": true,
    "mock": false,
    "use_solver": true,
    "headless": true,
    "video_limit": 10,
    "comments_per_video": 5,
    "comment_pages": 3
  }'
```

---

## ☁️ Despliegue (Heroku u otros)

Para **Heroku** (solo API o API+mock; scraping headless en Heroku requiere buildpacks extra de Chromium y puede no ser estable):

1. `Procfile`

   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

2. `runtime.txt`

   ```
   python-3.12.3
   ```

3. Variables:

   * `ENV=prod`
   * (Opcional) `ANTICAPTCHA_API_KEY` si se intentara scraping con solver (no recomendado en Heroku básico).

> Recomendación: en Heroku usar `run_scrapers=false` y `mock=true` para la demo. Ejecutar scraping localmente y subir los `*_features.json` como cache si se desea.

---

## 🩺 Troubleshooting

* **“Could not import module 'main'”**
  Lanza con:

  ```bash
  export PYTHONPATH=$(pwd)
  uvicorn app.main:app --reload --port 8000
  ```

* **404 en `/healthz`**
  Tienes dos rutas: `/healthz` y `/api/healthz`. Usa cualquiera.

* **`ModuleNotFoundError: services.*`**
  Asegúrate de ejecutar desde `backend/` y con `PYTHONPATH` correcto.
  Los scrapers añaden la ruta del proyecto al `sys.path` al inicio (ya incluido).

* **CAPTCHA / “Challenge no resuelto”**

  * Opción A: `--interactive true` y resuelve manualmente.
  * Opción B: `--use-solver true` + `ANTICAPTCHA_API_KEY`.
  * Opción C: para demo usa `run_scrapers=false`/`mock=true`.

---

## 🔒 Seguridad

* **Nunca** subas claves a Git. Usa `.env` o secretos del proveedor.
* Revisa `.gitignore` para artefactos (`*.csv`, caches, perfiles de navegador, etc.).

---

## 📄 Licencia

Uso educativo / hackathon. Adapta a tus necesidades antes de producción.

---

## 👥 Autores

Equipo HackIAthon — PyME Risk Scoring.
¡Gracias por probarlo!
