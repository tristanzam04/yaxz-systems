"""
Yaxz Systems · Revisor de Contratos con IA
Firebase Cloud Function (Python) que envuelve el backend FastAPI.
Sirve el frontend desde Firebase Hosting + ejecuta la API.
"""

from firebase_functions import https_fn
from firebase_admin import initialize_app, credentials, firestore, auth
import os

# Init
initialize_app()

# Importar la app FastAPI
import sys
sys.path.insert(0, os.path.dirname(__file__))
from backend.main import app

@https_fn.on_request()
def api(req: https_fn.Request) -> https_fn.Response:
    """Adaptador ASGI -> WSGI para Firebase Functions."""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.request(
        method=req.method,
        url=req.url,
        headers=dict(req.headers),
        content=req.get_data()
    )
    return https_fn.Response(
        response.content,
        status=response.status_code,
        headers=dict(response.headers)
    )
