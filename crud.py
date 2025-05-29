from fastapi import HTTPException
from typing import Optional, List
from models import User, Task, Note
from database import db
from datetime import datetime

# ——— Usuarios ———

def get_all_users():
    return [doc.to_dict() | {"id": doc.id} for doc in db.collection("users").stream()]

def get_user_by_id(user_id):
    doc = db.collection("users").document(user_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return doc.to_dict() | {"id": doc.id}

def create_user(user: User):
    new_ref = db.collection("users").document()
    new_ref.set(user.dict())
    return {"id": new_ref.id, **user.dict()}

def update_user(user_id: str, user: User):
    ref = db.collection("users").document(user_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    ref.update(user.dict())
    return {"status": "updated"}

def delete_user(user_id: str):
    ref = db.collection("users").document(user_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    ref.delete()
    return {"status": "deleted"}

def login_user(email: str, password: str):
    users_ref = db.collection("users")
    query = users_ref.where("email", "==", email).where("password", "==", password).stream()
    found = [doc for doc in query]
    if not found:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return {"status": "success", "user_id": found[0].id}



# ——— Tareas ———

VALID_STATUSES    = ["Pendiente", "En progreso", "Completada"]
VALID_PRIORITIES  = ["Baja", "Media", "Alta"]

def normalize_status(status: str) -> str:
    sl = status.lower()
    if sl in ["pendiente", "pendientes"]:
        return "Pendiente"
    if "en progreso" in sl:
        return "En progreso"
    if sl in ["completa", "completada"]:
        return "Completada"
    return "Pendiente"

def normalize_priority(priority: str) -> str:
    pl = priority.capitalize()
    return pl if pl in VALID_PRIORITIES else "Media"

def get_all_tasks() -> List[dict]:
    return [doc.to_dict() | {"id": doc.id} for doc in db.collection("tareas").stream()]

def get_task_by_id(task_id: str) -> dict:
    doc = db.collection("tareas").document(task_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return doc.to_dict() | {"id": doc.id}

def create_task(task: Task) -> dict:
    data = task.dict()

    # Normaliza y valida status
    data["status"] = normalize_status(data.get("status", "Pendiente"))
    if data["status"] not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Usa uno de {VALID_STATUSES}")

    # Normaliza y valida priority
    data["priority"] = normalize_priority(data.get("priority", "Media"))
    if data["priority"] not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Prioridad inválida. Usa uno de {VALID_PRIORITIES}")

    # Asegurar tags como lista
    tags = data.get("tags")
    data["tags"] = tags if isinstance(tags, list) else []

    # Procesar steps como lista de dicts válidos
    steps = data.get("steps")
    normalized_steps = []
    if isinstance(steps, list):
        for s in steps:
            if isinstance(s, dict) and "description" in s:
                normalized_steps.append({
                    "description": s["description"],
                    "completed": bool(s.get("completed", False))
                })
    data["steps"] = normalized_steps

    # Verifica formato de due_date
    try:
        datetime.strptime(data["due_date"], "%d-%m-%Y")
    except ValueError:
        raise HTTPException(status_code=400, detail="La fecha debe estar en formato dd-mm-YYYY")

    # Guarda en Firestore
    ref = db.collection("tareas").document()
    ref.set(data)
    return {"id": ref.id, **data}

def update_task(task_id: str, task: Task) -> dict:
    ref = db.collection("tareas").document(task_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    data = task.dict()

    # Normaliza y valida status
    data["status"] = normalize_status(data.get("status", "Pendiente"))
    if data["status"] not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Usa uno de {VALID_STATUSES}")

    # Normaliza y valida priority
    data["priority"] = normalize_priority(data.get("priority", "Media"))
    if data["priority"] not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Prioridad inválida. Usa uno de {VALID_PRIORITIES}")

    # Asegurar tags como lista
    tags = data.get("tags")
    data["tags"] = tags if isinstance(tags, list) else []

    # Procesar steps como lista de dicts válidos
    steps = data.get("steps")
    normalized_steps = []
    if isinstance(steps, list):
        for s in steps:
            if isinstance(s, dict) and "description" in s:
                normalized_steps.append({
                    "description": s["description"],
                    "completed": bool(s.get("completed", False))
                })
    data["steps"] = normalized_steps

    # Verifica formato de due_date
    try:
        datetime.strptime(data["due_date"], "%d-%m-%Y")
    except ValueError:
        raise HTTPException(status_code=400, detail="La fecha debe estar en formato dd-mm-YYYY")

    ref.update(data)
    return {"status": "updated"}

def delete_task(task_id: str) -> dict:
    ref = db.collection("tareas").document(task_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    ref.delete()
    return {"status": "deleted"}

def get_tasks_by_user(user_id: str, tag: Optional[str] = None, status: Optional[str] = None) -> List[dict]:
    query = db.collection("tareas").where("user_id", "==", user_id)
    if tag:
        query = query.where("tags", "array_contains", tag)
    if status:
        ns = normalize_status(status)
        query = query.where("status", "==", ns)
    return [doc.to_dict() | {"id": doc.id} for doc in query.stream()]

def get_tasks_by_status(status: Optional[str] = None) -> List[dict]:
    q = db.collection("tareas")
    if status and status != "Todas":
        ns = normalize_status(status)
        q = q.where("status", "==", ns)
    return [doc.to_dict() | {"id": doc.id} for doc in q.stream()]



# ——— Notas ———

def get_all_notes() -> List[dict]:
    """Devuelve todas las notas almacenadas."""
    return [doc.to_dict() | {"id": doc.id} for doc in db.collection("notes").stream()]

def get_note_by_id(note_id: str) -> dict:
    """Devuelve una nota por su ID."""
    doc = db.collection("notes").document(note_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return doc.to_dict() | {"id": doc.id}

def create_note(user_id: str, title: str, texto: str, tags: Optional[List[str]] = None) -> dict:
    """Crea una nueva nota con los campos definidos en el modelo."""
    now = datetime.utcnow().isoformat()
    data = {
        "user_id": user_id,
        "title": title,
        "texto": texto,
        "tags": tags or [],
        "created_at": now,
        "updated_at": now
    }
    ref = db.collection("notes").document()
    ref.set(data)
    return {"id": ref.id, **data}

def update_note(note_id: str, title: str, texto: str, tags: Optional[List[str]] = None) -> dict:
    """Actualiza los campos `title`, `texto` y `tags` de una nota existente."""
    ref = db.collection("notes").document(note_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Nota no encontrada")

    update_data = {
        "updated_at": datetime.utcnow().isoformat(),
        "texto": texto,
        "title": title,
        "tags": tags or []
    }
    ref.update(update_data)
    return {"status": "updated", **update_data}

def delete_note(note_id: str) -> dict:
    """Elimina una nota por su ID."""
    ref = db.collection("notes").document(note_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    ref.delete()
    return {"status": "deleted"}