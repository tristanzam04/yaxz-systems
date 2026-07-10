"""
Yaxz Systems · Revisor de Contratos con IA (Ollama + Firebase)
Backend FastAPI con auth (Firebase Auth) y rate limit (Firestore).

Sirve tanto el frontend del MVP como la API.
"""

import os
import io
import json
import re
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pdfplumber
from docx import Document
import requests
from dotenv import load_dotenv

# Firebase Admin (opcional - solo se usa si está configurado)
try:
    import firebase_admin
    from firebase_admin import credentials, auth, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

load_dotenv()

# ============================================================
# Configuración
# ============================================================
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
DAILY_LIMIT = 3

# ============================================================
# FastAPI
# ============================================================
app = FastAPI(title="Yaxz Systems · Revisor de Contratos", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ============================================================
# Firebase (init lazy)
# ============================================================
firebase_app = None
db = None

def init_firebase():
    global firebase_app, db
    if not FIREBASE_AVAILABLE or firebase_app is not None:
        return
    creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    try:
        try:
            default_app = firebase_admin.get_app()
            firebase_app = default_app
            db = firestore.client()
            print(f"[OK] Firebase ya estaba inicializado (usando app por defecto)")
            return
        except ValueError:
            pass

        if creds_path and os.path.exists(creds_path):
            cred = credentials.Certificate(creds_path)
            firebase_app = firebase_admin.initialize_app(cred)
        elif project_id:
            cred = credentials.ApplicationDefault()
            firebase_app = firebase_admin.initialize_app(cred, {"projectId": project_id})
        if firebase_app:
            db = firestore.client()
            print(f"[OK] Firebase inicializado")
    except Exception as e:
        print(f"[WARN] Firebase no se pudo inicializar: {e}")

# ============================================================
# Modelos
# ============================================================
class AuthRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = ""

class LeadRequest(BaseModel):
    vertical: str
    nombre: str
    empresa: str
    email: str
    whatsapp: str
    proceso: str
    tamano: str
    costo: int
    digital: str
    descripcion: Optional[str] = ""
    conservativeSavings: int
    potentialSavings: int
    findings: list
    verdict: dict

# ============================================================
# Auth
# ============================================================
async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Falta token de autenticación")
    token = authorization.replace("Bearer ", "").strip()

    if firebase_app is not None:
        try:
            decoded = auth.verify_id_token(token)
            return {"email": decoded.get("email"), "uid": decoded.get("uid"), "dev_mode": False}
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Token inválido: {e}")

    # Modo dev
    if token.startswith("dev:"):
        email = token[4:].strip()
        return {"email": email, "uid": f"dev-{email}", "dev_mode": True}
    raise HTTPException(status_code=401, detail="Token inválido (modo dev requiere Bearer dev:email)")

# ============================================================
# Rate limit
# ============================================================
def get_today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def check_and_increment_usage(user: dict) -> dict:
    today = get_today_key()
    uid = user["uid"]

    if user.get("dev_mode"):
        if not hasattr(app, "_dev_usage"):
            app._dev_usage = {}
        key = f"{uid}:{today}"
        current = app._dev_usage.get(key, 0)
        if current >= DAILY_LIMIT:
            raise HTTPException(status_code=429, detail=f"Has alcanzado el límite diario de {DAILY_LIMIT} análisis. Vuelve mañana.")
        app._dev_usage[key] = current + 1
        return {"used": current + 1, "limit": DAILY_LIMIT, "remaining": max(0, DAILY_LIMIT - current - 1), "date": today}

    if db is None:
        raise HTTPException(status_code=503, detail="Firestore no disponible")
    doc_ref = db.collection("usage").document(uid).collection("daily").document(today)
    doc = doc_ref.get()
    used = doc.to_dict().get("count", 0) if doc.exists else 0
    if used >= DAILY_LIMIT:
        raise HTTPException(status_code=429, detail=f"Has alcanzado el límite diario de {DAILY_LIMIT} análisis. Vuelve mañana.")
    doc_ref.set({"count": used + 1, "email": user["email"], "updated_at": datetime.now(timezone.utc).isoformat()}, merge=True)
    return {"used": used + 1, "limit": DAILY_LIMIT, "remaining": max(0, DAILY_LIMIT - used - 1), "date": today}

def get_usage(user: dict) -> dict:
    today = get_today_key()
    uid = user["uid"]
    if user.get("dev_mode"):
        if not hasattr(app, "_dev_usage"):
            app._dev_usage = {}
        key = f"{uid}:{today}"
        used = app._dev_usage.get(key, 0)
        return {"used": used, "limit": DAILY_LIMIT, "remaining": max(0, DAILY_LIMIT - used), "date": today}
    if db is None:
        return {"used": 0, "limit": DAILY_LIMIT, "remaining": DAILY_LIMIT, "date": today}
    doc_ref = db.collection("usage").document(uid).collection("daily").document(today)
    doc = doc_ref.get()
    used = doc.to_dict().get("count", 0) if doc.exists else 0
    return {"used": used, "limit": DAILY_LIMIT, "remaining": max(0, DAILY_LIMIT - used), "date": today}

# ============================================================
# Extracción de texto
# ============================================================
def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t: text += t + "\n\n"
    return text.strip()

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())

def extract_text_from_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="ignore").strip()

def extract_text(file_bytes: bytes, filename: str) -> tuple[str, str]:
    fn = filename.lower()
    if fn.endswith(".pdf"): return extract_text_from_pdf(file_bytes), "pdf"
    if fn.endswith(".docx"): return extract_text_from_docx(file_bytes), "docx"
    if fn.endswith(".doc"): raise HTTPException(status_code=400, detail=".doc no soportado. Usa .docx o .pdf")
    if fn.endswith(".txt") or fn.endswith(".md"): return extract_text_from_txt(file_bytes), "txt"
    raise HTTPException(status_code=400, detail=f"Tipo no soportado: {filename}")

# ============================================================
# Análisis con Ollama
# ============================================================
ANALYSIS_INSTRUCTION = """Eres un abogado senior mexicano especializado en revisión de contratos. Conoces la LFPDPPP, el Código Civil Federal, la Ley Federal del Trabajo, el Código de Comercio y la jurisprudencia mexicana.

IMPORTANTE: Responde ÚNICAMENTE con un JSON válido. Sin texto antes ni después. Sin bloques markdown.

Analiza el siguiente contrato mexicano y devuelve un JSON con esta estructura EXACTA:

{
  "summary": "Resumen ejecutivo de 2-3 oraciones.",
  "overall_score": <entero 0-100, donde 100 = muy seguro, 0 = muy riesgoso>,
  "risk_level": "<low|medium|high>",
  "clauses": [
    {
      "name": "<nombre de la cláusula>",
      "category": "<Protección|Salida|Riesgo|Legal|Financiero|Propiedad|Restricción|Temporal|Operacional>",
      "risk": "<low|medium|high>",
      "snippet": "<texto exacto, máx 200 chars>",
      "explanation": "<por qué tiene ese nivel de riesgo, 1-2 oraciones>"
    }
  ],
  "red_flags": [
    {
      "severity": "<high|medium>",
      "title": "<título corto>",
      "description": "<explicación en contexto mexicano>"
    }
  ],
  "questions_for_lawyer": [
    "<pregunta que el abogado debería hacerse>"
  ]
}

Reglas:
- Mínimo 5 cláusulas, máximo 15.
- Red flags: problemas serios que un junior pasaría por alto.
- Si no puedes identificar algo con certeza, omítelo.

Contrato:

---
CONTRACT_TEXT_PLACEHOLDER
---

Responde SOLO el JSON."""

PLAYBOOK_INSTRUCTION_TEMPLATE = """Eres un abogado senior mexicano especializado en revisión de contratos. Conoces la LFPDPPP, el Código Civil Federal, la Ley Federal del Trabajo, el Código de Comercio y la jurisprudencia mexicana.

Tu tarea es auditar el siguiente contrato y compararlo estrictamente contra el Playbook (directrices) que el usuario ha provisto.

DIRECTRICES DEL PLAYBOOK:
PLAYBOOK_TEXT_PLACEHOLDER

IMPORTANTE: Responde ÚNICAMENTE con un JSON válido. Sin texto antes ni después. Sin bloques markdown.

Analiza el contrato y devuelve un JSON con esta estructura EXACTA:

{
  "summary": "Resumen de la alineación general con el playbook e implicaciones operativas (2-3 oraciones).",
  "overall_score": <entero 0-100, donde 100 = 100% de cumplimiento con las directrices, 0 = incumplimiento total>,
  "risk_level": "<low|medium|high>",
  "clauses": [
    {
      "name": "<nombre de la cláusula o directriz evaluada>",
      "category": "<Protección|Salida|Riesgo|Legal|Financiero|Propiedad|Restricción|Temporal|Operacional>",
      "risk": "<low|medium|high>",
      "snippet": "<texto exacto del contrato relacionado con la directriz, máx 200 chars>",
      "explanation": "<cómo se alinea o viola la directriz en el contexto mexicano, 1-2 oraciones>"
    }
  ],
  "red_flags": [
    {
      "severity": "<high|medium>",
      "title": "<título corto de la desviación o riesgo>",
      "description": "<explicación de por qué viola el playbook o representa riesgo bajo la ley mexicana>"
    }
  ],
  "questions_for_lawyer": [
    "<pregunta o sugerencia para negociar esta desviación>"
  ]
}

Reglas:
- Evalúa el contrato contra CADA directriz del playbook. Muestra cuáles se cumplen y cuáles se violan.
- Si hay cláusulas en el contrato que representan riesgos graves no contemplados por el playbook, agrégalas también en las cláusulas de riesgo o red_flags.
- Mínimo 5 cláusulas, máximo 15.

Contrato:

---
CONTRACT_TEXT_PLACEHOLDER
---

Responde SOLO el JSON."""

def analyze_with_ollama(contract_text: str, playbook_text: Optional[str] = None) -> dict:
    max_chars = 32000
    if len(contract_text) > max_chars:
        contract_text = contract_text[:max_chars] + "\n\n[CONTRATO TRUNCADO]"
    
    if playbook_text and playbook_text.strip():
        user_prompt = PLAYBOOK_INSTRUCTION_TEMPLATE.replace("PLAYBOOK_TEXT_PLACEHOLDER", playbook_text.strip()).replace("CONTRACT_TEXT_PLACEHOLDER", contract_text)
    else:
        user_prompt = ANALYSIS_INSTRUCTION.replace("CONTRACT_TEXT_PLACEHOLDER", contract_text)

    try:
        headers = {}
        api_key = os.getenv("OLLAMA_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        resp = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            headers=headers,
            json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": user_prompt}],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1}
            },
            timeout=180
        )
        resp.raise_for_status()
        response_text = resp.json()["message"]["content"].strip()
        response_text = re.sub(r"^```json\s*", "", response_text)
        response_text = re.sub(r"^```\s*", "", response_text)
        response_text = re.sub(r"\s*```$", "", response_text)
        analysis = json.loads(response_text)
        if "overall_score" not in analysis or "clauses" not in analysis:
            raise ValueError("Estructura inesperada")
        analysis["overall_score"] = int(analysis.get("overall_score", 50))
        analysis["risk_level"] = analysis.get("risk_level", "medium")
        analysis["clauses"] = analysis.get("clauses", [])
        analysis["red_flags"] = analysis.get("red_flags", [])
        analysis["questions_for_lawyer"] = analysis.get("questions_for_lawyer", [])
        analysis["summary"] = analysis.get("summary", "")
        return analysis
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail=f"No se pudo conectar a Ollama en {OLLAMA_HOST}. ¿Está corriendo?")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Ollama tardó demasiado. ¿Contrato muy largo?")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Ollama devolvió JSON inválido: {str(e)[:200]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error con Ollama: {str(e)}")

# ============================================================
# Endpoints
# ============================================================
@app.on_event("startup")
def startup():
    init_firebase()
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            print(f"[OK] Ollama en {OLLAMA_HOST}. Modelos: {models[:3]}")
            if OLLAMA_MODEL not in models:
                print(f"[WARN] '{OLLAMA_MODEL}' no descargado. Ejecuta: ollama pull {OLLAMA_MODEL}")
    except Exception as e:
        print(f"[WARN] Ollama no accesible: {e}")

@app.get("/api/health")
def health():
    ollama_ok = False
    ollama_models = []
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        if r.status_code == 200:
            ollama_ok = True
            ollama_models = [m["name"] for m in r.json().get("models", [])]
    except: pass
    return {
        "status": "ok",
        "service": "Yaxz Contract Analyzer",
        "ollama": {"host": OLLAMA_HOST, "model": OLLAMA_MODEL, "connected": ollama_ok, "models": ollama_models[:3]},
        "firebase": {"configured": firebase_app is not None, "dev_mode": firebase_app is None},
        "rate_limit": DAILY_LIMIT
    }

@app.post("/api/leads")
def save_lead(req: LeadRequest):
    if db is not None:
        try:
            lead_ref = db.collection("leads").document()
            lead_ref.set({
                "vertical": req.vertical,
                "nombre": req.nombre,
                "empresa": req.empresa,
                "email": req.email,
                "whatsapp": req.whatsapp,
                "proceso": req.proceso,
                "tamano": req.tamano,
                "costo": req.costo,
                "digital": req.digital,
                "descripcion": req.descripcion,
                "conservative_savings": req.conservativeSavings,
                "potential_savings": req.potentialSavings,
                "findings": req.findings,
                "verdict": req.verdict,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            return {"status": "success", "id": lead_ref.id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar lead: {e}")
    else:
        print(f"[DEV MODE] Lead recibido: {req.nombre} ({req.email}) de {req.empresa}")
        return {"status": "success", "dev": True, "lead": req.dict()}

@app.post("/api/register")
def register(req: AuthRequest):
    if "@" not in req.email or "." not in req.email:
        raise HTTPException(status_code=400, detail="Email inválido")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Contraseña mínimo 6 caracteres")
    if not req.name or len(req.name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Nombre requerido")

    if firebase_app is not None:
        try:
            user_record = auth.create_user(email=req.email, password=req.password, display_name=req.name)
            if db is not None:
                db.collection("users").document(user_record.uid).set({
                    "email": req.email, "name": req.name,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
            custom_token = auth.create_custom_token(user_record.uid)
            return {"token": f"Bearer {custom_token.decode()}", "user": {"email": req.email, "name": req.name, "uid": user_record.uid}}
        except auth.EmailAlreadyExistsError:
            raise HTTPException(status_code=409, detail="Este email ya está registrado")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error registrando: {e}")
    else:
        if not hasattr(app, "_dev_users"):
            app._dev_users = {}
        if req.email in app._dev_users:
            raise HTTPException(status_code=409, detail="Este email ya está registrado")
        uid = f"dev-{len(app._dev_users)+1}"
        app._dev_users[req.email] = {"email": req.email, "name": req.name, "password": req.password, "uid": uid}
        return {"token": f"Bearer dev:{req.email}", "user": {"email": req.email, "name": req.name, "uid": uid, "dev_mode": True}}

@app.post("/api/login")
def login(req: AuthRequest):
    if firebase_app is not None:
        api_key = os.getenv("FIREBASE_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="FIREBASE_API_KEY no configurada")
        try:
            r = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
                json={"email": req.email, "password": req.password, "returnSecureToken": True},
                timeout=10
            )
            if r.status_code != 200:
                raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
            id_token = r.json()["idToken"]
            decoded = auth.verify_id_token(id_token)
            return {"token": f"Bearer {id_token}", "user": {"email": decoded.get("email"), "name": decoded.get("name", req.email), "uid": decoded.get("uid")}}
        except HTTPException:
            raise
        except:
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    else:
        if not hasattr(app, "_dev_users") or req.email not in app._dev_users:
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
        user = app._dev_users[req.email]
        if user["password"] != req.password:
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
        return {"token": f"Bearer dev:{req.email}", "user": {"email": user["email"], "name": user["name"], "uid": user["uid"], "dev_mode": True}}

# Fix usage endpoints to use proper auth
from fastapi import Depends
async def dep_user(authorization: Optional[str] = Header(None)):
    return await get_current_user(authorization)

@app.get("/api/usage")
def my_usage(user: dict = Depends(dep_user)):
    usage = get_usage(user)
    return {"email": user["email"], **usage}

@app.post("/api/analyze")
async def analyze_contract(
    file: UploadFile = File(...),
    playbook: Optional[str] = Form(None),
    user: dict = Depends(dep_user)
):
    usage = check_and_increment_usage(user)
    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Máx 10 MB")
    try:
        text, ftype = extract_text(file_bytes, file.filename)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extrayendo texto: {e}")
    if not text or len(text.strip()) < 200:
        raise HTTPException(status_code=400, detail="Texto insuficiente (mín 200 chars)")
    analysis = analyze_with_ollama(text, playbook)
    return {
        "file_name": file.filename, "file_type": ftype,
        "word_count": len(text.split()),
        "reading_time_min": round(max(0.5, len(text.split()) / 200), 1),
        "overall_score": analysis["overall_score"],
        "risk_level": analysis["risk_level"],
        "summary": analysis["summary"],
        "clauses": analysis["clauses"],
        "red_flags": analysis["red_flags"],
        "questions_for_lawyer": analysis["questions_for_lawyer"],
        "metadata": {"chars_extracted": len(text), "model": OLLAMA_MODEL},
        "usage": usage
    }

# ============================================================
# Frontend estático
# ============================================================
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/brand", StaticFiles(directory=os.path.join(FRONTEND_DIR, "brand")), name="brand")
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def serve_index():
    idx = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(idx):
        return FileResponse(idx)
    return {"message": "Yaxz API", "frontend": "not found"}

@app.get("/{filename}")
async def serve_file(filename: str):
    fpath = os.path.join(FRONTEND_DIR, filename)
    if os.path.exists(fpath) and os.path.isfile(fpath):
        return FileResponse(fpath)
    raise HTTPException(status_code=404, detail="File not found")

# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
