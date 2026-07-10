# SVC · Despliegue en Firebase

## 📁 Estructura actual

```
app\
├── index.html              ← Landing + diagnóstico
├── mvp\
│   ├── frontend\           ← UI del MVP (HTML estático)
│   │   └── index.html
│   ├── backend\            ← API FastAPI + Ollama
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── .env.example
│   ├── functions\          ← Firebase Functions (envuelve backend)
│   │   ├── main.py
│   │   └── package.json
│   ├── firebase.json       ← Configuración Firebase
│   ├── firestore.rules     ← Reglas de seguridad
│   ├── firestore.indexes.json
│   └── .firebaserc         ← Project ID
└── (otros archivos)

brand\                       ← Logo y guía
docs\                        ← Documentación
```

## 🚀 Pasos para desplegar

### 1. Instalar herramientas (una sola vez)

```bash
# Node.js (necesario para Firebase CLI)
# Descargar de https://nodejs.org/

# Firebase CLI
npm install -g firebase-tools

# Python 3.11 (ya lo tienes)
# Ollama (ya lo tienes): https://ollama.com/download
```

### 2. Crear proyecto Firebase

1. Ve a https://console.firebase.google.com/
2. Click **"Agregar proyecto"** → nombre: `svc-consulting-mvp` (o el que quieras)
3. Desactiva Google Analytics (no lo necesitas)
4. Espera a que se cree

### 3. Habilitar servicios

En la consola del proyecto:

- **Authentication** → Sign-in method → Habilitar **Email/Password**
- **Firestore Database** → Crear base de datos → Modo producción → Ubicación: `us-central1` (o la más cercana)

### 4. Configurar el proyecto

Edita `app/mvp/.firebaserc` y pon tu project ID real:

```json
{
  "projects": {
    "default": "TU-PROJECT-ID-AQUI"
  }
}
```

### 5. Obtener credenciales de servicio

En Firebase Console:
- ⚙️ Project Settings → Service Accounts → **Generate new private key**
- Se descarga un JSON. **Renómbralo a `serviceAccountKey.json`**
- **NO lo subas a git** (agrégalo a `.gitignore`)

Cópialo a `app/mvp/backend/serviceAccountKey.json`

### 6. Obtener API Key del frontend

En Firebase Console:
- ⚙️ Project Settings → General → **Web API Key**
- Cópiala (es un string largo que empieza con `AIzaSy...`)

### 7. Configurar el backend

Edita `app/mvp/backend/.env` (copia de `.env.example`):

```env
# Ollama: apunta a donde esté corriendo tu servidor Ollama
# Si vas a usar Ollama Cloud: https://ollama.com/cloud
# Si vas a usar tu propio servidor: pon la IP/dominio público
OLLAMA_HOST=https://tu-ollama-publica.com
OLLAMA_MODEL=llama3.1:8b

# Firebase
FIREBASE_CREDENTIALS_PATH=./serviceAccountKey.json
FIREBASE_PROJECT_ID=tu-project-id
FIREBASE_API_KEY=AIzaSy... (la que copiaste en paso 6)

PORT=8000
```

### 8. Decidir dónde corre Ollama

Opciones:

| Opción | Costo | Setup | Recomendado para |
|---|---|---|---|
| **Tu PC** + ngrok | Gratis | Fácil | Demo personal |
| **Oracle Cloud Free Tier** | Gratis permanente | Medio | Producción pequeña |
| **Railway** | $5/mes | Muy fácil | MVP rápido |
| **Render** | $7/mes | Fácil | MVP rápido |
| **VPS (DigitalOcean, Hetzner)** | $4-6/mes | Medio | Producción |

**Para empezar rápido (recomendado): Railway con Ollama**

```bash
# Crear Dockerfile en app/mvp/backend/
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl
RUN curl -fsSL https://ollama.com/install.sh | sh
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN ollama serve & sleep 10 && ollama pull llama3.1:8b
EXPOSE 8000
CMD ["python", "main.py"]
EOF

# Deploy a Railway
railway login
railway init
railway up
```

### 9. Configurar el frontend para apuntar al backend

Edita `app/mvp/frontend/index.html` y cambia:

```javascript
const API_BASE = window.location.origin;
```

Si tu backend está en otro dominio (ej: `api.svc.consulting`), cámbialo a:

```javascript
const API_BASE = 'https://api.svc.consulting';
```

### 10. Deploy a Firebase

```bash
cd app/mvp
firebase login
firebase deploy
```

Esto sube:
- **Hosting:** el frontend a `https://tu-proyecto.web.app`
- **Functions:** el backend (si lo configuraste como Cloud Function)
- **Firestore rules:** las reglas de seguridad
- **Firestore indexes:** los índices

### 11. Probar

Abre `https://tu-proyecto.web.app` y:

1. Click en "Crear cuenta"
2. Regístrate con un email
3. Sube un PDF de prueba
4. Espera ~30 segundos
5. Verás el análisis con cláusulas, score, alertas

## 🔒 Reglas de seguridad (ya configuradas)

`firestore.rules`:
- Usuarios solo pueden leer/escribir su propio documento
- Rate limit solo es modificable por el dueño del UID
- Sin auth = sin acceso

## 💰 Costos estimados

| Servicio | Plan gratuito | Costo si excedes |
|---|---|---|
| Firebase Hosting | 10 GB/mes | $0.15/GB |
| Firebase Functions | 2M invocaciones/mes | $0.40/M |
| Firebase Auth | 50K usuarios | Gratis hasta 50K |
| Firestore | 1 GB + 50K lecturas/día | $0.18/GB |
| Ollama (tu infra) | $0 | Tu costo de servidor |

**Total para 100-1000 análisis/mes: $0-10 USD**

## 🐛 Troubleshooting

### "Firebase no se pudo inicializar"
- Verifica que `serviceAccountKey.json` existe en `app/mvp/backend/`
- Verifica que la ruta en `.env` sea correcta

### "Ollama no accesible"
- Verifica que Ollama esté corriendo: `ollama serve`
- Si está en otro servidor, verifica firewall y que el puerto 11434 esté abierto

### "CORS error"
- El backend tiene `CORSMiddleware` con `allow_origins=["*"]`
- En producción, cambia a tu dominio específico

### "Rate limit no funciona en producción"
- Verifica que Firestore esté habilitado
- Verifica que las reglas de seguridad permitan al usuario escribir en su propio `/usage/{uid}/daily/{date}`

## 📞 Contacto

Tristán Zamora
tristan@yaxz.systems
+52 56 4950 4535
