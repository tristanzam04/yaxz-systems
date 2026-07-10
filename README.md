# Yaxz Systems · Guía para Principiantes 🚀

¡Bienvenido al repositorio de **Yaxz Systems**! Este proyecto es un revisor inteligente de contratos que utiliza Inteligencia Artificial (Ollama / DeepSeek) y una arquitectura moderna basada en FastAPI y Firebase.

Esta guía está diseñada para que puedas configurar el proyecto en cualquier computadora desde cero de manera súper sencilla.

---

## 📁 Estructura del Proyecto

```text
yaxz-systems/
├── app/
│   ├── index.html              ← Landing pública + diagnóstico inicial
│   └── mvp/                    ← MVP del revisor de contratos con IA
│       ├── backend/            ← API hecha en FastAPI (Python)
│       │   ├── main.py         ← Archivo principal de la API
│       │   └── requirements.txt← Dependencias de Python
│       ├── frontend/           ← Interfaz del revisor (HTML/JS estático)
│       └── DEPLOY.md           ← Instrucciones técnicas de Firebase
├── brand/                      ← Logotipos y paleta de colores
├── docs/                       ← Documentación de metodología y pitch decks
├── package.json                ← Comandos automatizados de NPM
└── .gitignore                  ← Archivos que no se suben a GitHub
```

---

## 🛠️ Requisitos Previos (Una sola vez)

Antes de empezar, asegúrate de tener instalado lo siguiente en tu computadora:

1. **Git**: [Descargar Git](https://git-scm.com/) (necesario para descargar y subir cambios a GitHub).
2. **Node.js**: [Descargar Node.js](https://nodejs.org/) (necesario para ejecutar los comandos de NPM y Firebase).
3. **Python 3.11**: [Descargar Python](https://www.python.org/) (necesario para correr el backend/API).
4. **Ollama**: [Descargar Ollama](https://ollama.com/) (si deseas correr modelos de lenguaje de manera local).

---

## 🚀 Guía de Configuración en una Nueva Computadora

Sigue estos pasos en orden para poner a funcionar el proyecto:

### 1. Clonar el repositorio
Abre una terminal y clona el proyecto de tu cuenta de GitHub:
```bash
git clone https://github.com/tristanzam04/yaxz-systems.git
cd yaxz-systems
```

### 2. Instalar dependencias
Para instalar automáticamente todas las dependencias de Python necesarias para el backend, ejecuta:
```bash
npm run install-all
```

### 3. Configurar variables de entorno (`.env`)
Por seguridad, las claves de las APIs no se suben a GitHub. Ve a la carpeta `app/mvp/backend/`, crea un archivo llamado `.env` y copia los valores del archivo `.env.example`.
Deberá verse similar a esto:
```env
OLLAMA_HOST=https://tu-ollama-publica.com
OLLAMA_MODEL=llama3.1:8b
FIREBASE_CREDENTIALS_PATH=./serviceAccountKey.json
FIREBASE_PROJECT_ID=tu-project-id
FIREBASE_API_KEY=tu-api-key
PORT=8000
```

---

## 💻 Comandos Útiles (`npm run`)

Hemos configurado comandos automáticos iguales a los de **TGS App** para facilitarte la vida. Ejecútalos desde la carpeta raíz del proyecto:

### 🟢 Para el Desarrollo Diario:
*   `npm run dev`: Inicia el servidor del backend en FastAPI y monta automáticamente la interfaz del frontend en el puerto `http://localhost:8000`.

### 🔄 Para Sincronizar con GitHub:
*   `npm run sync:pull`: Descarga los últimos cambios del repositorio de manera segura sin sobreescribir tus commits locales.
*   `npm run sync:push`: Agrega tus cambios locales, hace un commit automático y los sube a GitHub al instante.
*   `npm run sync:fix`: Limpia cualquier conflicto de archivos local y descarga la versión limpia directamente de GitHub.
*   `npm run sync:debug`: Muestra la información de tu entorno y conexión a Git para diagnosticar problemas.

### 🌐 Para Desplegar a Producción:
*   `npm run deploy`: Sube el frontend a Firebase Hosting y las funciones a Firebase Cloud Functions.

---

## 📞 Soporte e Información
Desarrollado por **Tristán Zamora**.
*   **Email:** tristan@yaxz.systems
*   **Teléfono:** +52 221 879 9202
