from google.cloud import firestore
from google.oauth2 import service_account
from dotenv import load_dotenv
import os

# ————— Carga de entorno —————
load_dotenv()

# ————— Variables de entorno —————
PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID")
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# ————— Debug de configuración —————
print(f"[Firestore] GOOGLE_APPLICATION_CREDENTIALS = {CREDENTIALS_PATH}")
print(f"[Firestore] PROJECT_ID               = {PROJECT_ID}")

# ————— Inicializar credenciales y cliente —————
credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
db = firestore.Client(project=PROJECT_ID, credentials=credentials)

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
