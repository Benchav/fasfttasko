import os
import json
from dotenv import load_dotenv
from google.cloud import firestore
from google.oauth2 import service_account

# ————— Carga de entorno —————
# Solo necesario en desarrollo local para .env
load_dotenv()

# ————— Detectar entorno —————
USE_EMULATOR = os.getenv("FIRESTORE_EMULATOR_HOST") is not None

if USE_EMULATOR:
    # — Emulador local —
    print("🔧 Conectando a Firestore en modo EMULADOR")
    # El project_id puede ser cualquiera en el emulador
    db = firestore.Client(project="demo-project")
else:
    # — Producción (Railway, etc.) —
    print("🚀 Conectando a Firestore en modo PRODUCCIÓN")

    # 1) Leer JSON de servicio desde la variable serviceAccountKey
    service_account_json = os.getenv("serviceAccountKey")
    if not service_account_json:
        raise RuntimeError("⚠️ Falta la variable de entorno `serviceAccountKey` con el JSON de credenciales")

    # Si lo almacenaste en Base64, descoméntalo:
    # import base64
    # service_account_json = base64.b64decode(service_account_json).decode("utf-8")

    info = json.loads(service_account_json)
    credentials = service_account.Credentials.from_service_account_info(info)

    # 2) Leer ID de proyecto
    project_id = os.getenv("FIRESTORE_PROJECT_ID")
    if not project_id:
        raise RuntimeError("⚠️ Falta la variable de entorno `FIRESTORE_PROJECT_ID`")

    db = firestore.Client(project=project_id, credentials=credentials)

# ————— Debug de configuración —————
print(f"[Firestore] Uso emulador? {USE_EMULATOR}")
if not USE_EMULATOR:
    print(f"[Firestore] Proyecto = {project_id}")

# ————— Función de utilidad: listar colecciones —————
def list_collections():
    """
    Devuelve una lista con el nombre de todas las colecciones en Firestore.
    Útil para depuración.
    """
    return [col.id for col in db.collections()]

# ————— Función de utilidad: muestreo de documentos —————
def sample_docs(collection_names=None, limit=1):
    """
    Para cada nombre en collection_names, devuelve hasta `limit` documentos.
    Si no se proporciona collection_names, usa todas las colecciones.
    Útil para comprobar rápidamente que tus colecciones tienen datos.
    """
    resp = {}
    names = collection_names or list_collections()
    for name in names:
        docs = db.collection(name).limit(limit).stream()
        resp[name] = [{**doc.to_dict(), "id": doc.id} for doc in docs] or "colección vacía"
    return resp