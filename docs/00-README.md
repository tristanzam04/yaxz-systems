# Yaxz Systems
## Lanzamiento · Julio 2026

---

## Estructura del proyecto

```
yaxz-systems\
│
├── app\
│   └── index.html              ← App principal (landing + diagnóstico)
│
├── app/mvp\                    ← MVP REAL con IA (Ollama/DeepSeek + FastAPI)
│   ├── backend\
│   │   ├── main.py             ← FastAPI app
│   │   ├── requirements.txt    ← Dependencias Python
│   │   ├── .env.example        ← Template de variables de entorno
│   │   └── README.md           ← Docs del backend
│   ├── frontend\
│   │   ├── index.html          ← Landing del MVP
│   │   ├── revisor.html        ← UI de Gobernanza Contractual
│   │   └── brand/              ← Logos y Favicons actualizados
│   └── README.md               ← Docs del MVP completo
│
├── brand\
│   ├── logo.svg                ← Logo Yaxz Systems (wordmark marino + gris)
│   ├── favicon.svg             ← Versión 32px para browser tab
│   └── brand-guide.md          ← Guía de uso de marca
│
└── docs\
    ├── 00-README.md            ← Este archivo
    ├── 01-metodologia-yaxz.md  ← Yaxz Framework (5 fases, 90 días)
    ├── 02-pitch-deck.md        ← Pitch de 12 slides (texto)
    ├── 03-casos-de-uso.md      ← Cuellos de botella por vertical
    └── 04-faq.md               ← Preguntas frecuentes
```

---

## Cómo está armado

### `app/index.html` y `app/mvp/frontend/index.html` — Las apps principales
Páginas HTML autocontenidas y optimizadas en Light Mode de alto contraste.
**Hacen dos cosas:**
1. Sirven de **landing pública** con propuesta de valor, hero, servicios y CTA bajo la marca Yaxz Systems.
2. Corren el **diagnóstico multi-vertical** (Construcción / Derecho / Comercio): 6 preguntas, motor de cálculo de ahorro, veredicto y captura de lead.

### `app/mvp` — El MVP real con IA
Backend FastAPI + Frontend HTML en Light Mode. Procesa contratos en PDF, Word y Texto con el modelo DeepSeek a través de la API oficial de Ollama Cloud.

**Stack:**
- Backend: Python 3.11 + FastAPI + pdfplumber + python-docx + Requests (Ollama Cloud API)
- Frontend: HTML estático en Light Mode con diseño premium y carga dinámica de playbooks.
- Deploy: Firebase Functions (API en Python) + Firebase Hosting.

---

## Cómo lo usas

### Para prospectar un cliente
1. Comparte el link de la app principal.
2. El prospecto hace su diagnóstico (o lo completas tú en 2 minutos en la llamada).
3. El reporte lo contacta por WhatsApp contigo.

### Para entrar a un despacho legal
1. Comparte el link de la herramienta de gobernanza contractual (`/revisor.html`).
2. Sube un contrato de prueba -> score de seguridad -> detección de alertas y fricciones operativas.
3. Los que toman en serio el reporte te contratan para auditorías y optimizaciones a fondo.

### Para presentar a un inversionista
1. Comparte `02-pitch-deck.md` y `01-metodologia-yaxz.md`.
2. Si hay fit, abre la app y el MVP en vivo.

---

## Contacto

Tristán Zamora
tristan@yaxz.systems
+52 56 4950 4535

Yaxz Systems · 2026
