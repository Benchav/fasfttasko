import os
import json
import traceback
from dotenv import load_dotenv
from google.cloud import firestore
from google.oauth2 import service_account

# ————— Carga de entorno —————
# En producción Vercel no usa .env, pero local sí.
load_dotenv()

USE_EMULATOR = bool(os.getenv("FIRESTORE_EMULATOR_HOST"))

try:
    if USE_EMULATOR:
        # Conexión a emulador local
        print("🔧 Conectando a Firestore en modo EMULADOR")
        db = firestore.Client(project="demo-project")
    else:
        # Conexión en producción usando ENV VAR con JSON
        print("🔐 Conectando a Firestore con credenciales desde ENV VARS")

        svc_json = os.getenv("SERVICE_ACCOUNT_KEY")
        if not svc_json:
            raise RuntimeError("⚠️ ENV VAR `SERVICE_ACCOUNT_KEY` vacía o no definida.")

        # Si tu JSON lo pusiste en Base64, decodifícalo:
        # import base64
        # svc_json = base64.b64decode(svc_json).decode("utf-8")

        info = json.loads(svc_json)
        creds = service_account.Credentials.from_service_account_info(info)

        project_id = os.getenv("FIRESTORE_PROJECT_ID")
        if not project_id:
            raise RuntimeError("⚠️ ENV VAR `FIRESTORE_PROJECT_ID` vacía o no definida.")

        db = firestore.Client(project=project_id, credentials=creds)

    print(f"[Firestore] Uso emulador? {USE_EMULATOR}")
    if not USE_EMULATOR:
        print(f"[Firestore] Proyecto = {project_id}")

except Exception as e:
    # Capturamos cualquier fallo en la inicialización y lo logeamos
    print("❌ Error inicializando Firestore:")
    traceback.print_exc()
    # Re-lanzamos para que Vercel marque la función como caída y veas el log
    raise

# ————— Función de utilidad: listar colecciones —————
def list_collections():
    return [col.id for col in db.collections()]

# ————— Función de utilidad: muestreo de documentos —————
def sample_docs(collection_names=None, limit=1):
    resp = {}
    names = collection_names or list_collections()
    for name in names:
        docs = db.collection(name).limit(limit).stream()
        resp[name] = [{**doc.to_dict(), "id": doc.id} for doc in docs] or "colección vacía"
    return resp