from fastapi import HTTPException
from typing import Optional, List
from models import User, Note, TaskCreate, TaskUpdate, TaskInDB, FocusTimeCreate, FocusTimeUpdate, FocusTimeInDB
from database import db
from datetime import datetime
from google.cloud.firestore_v1 import ArrayUnion
from typing import List, Dict
from models import FocusSummaryOut


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

# ——— CRUD de tareas ———

def get_all_tasks() -> List[dict]:
    """
    Devuelve todas las tareas con su id incluido.
    """
    return [doc.to_dict() | {"id": doc.id} for doc in db.collection("tareas").stream()]

def get_task_by_id(task_id: str) -> dict:
    """
    Obtiene la tarea por ID; lanza 404 si no existe.
    """
    doc = db.collection("tareas").document(task_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return doc.to_dict() | {"id": doc.id}

def create_task(task: TaskCreate) -> dict:
    """
    Crea una nueva tarea. Recibe TaskCreate (sin id) y devuelve dict con id y campos.
    """
    data = task.dict()

    # Normaliza y valida status
    data["status"] = normalize_status(data.get("status", "Pendiente"))
    if data["status"] not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Usa uno de {VALID_STATUSES}")

    # Normaliza y valida priority
    data["priority"] = normalize_priority(data.get("priority", "Media"))
    if data["priority"] not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Prioridad inválida. Usa uno de {VALID_PRIORITIES}")

    # Asegurar tags como lista de strings
    tags = data.get("tags")
    data["tags"] = tags if isinstance(tags, list) else []

    # Procesar steps como lista de dicts válidos
    steps = data.get("steps")
    normalized_steps = []
    if isinstance(steps, list):
        for s in steps:
            # Cada s es instancia de Step o dict equivalente validado por Pydantic
            if isinstance(s, dict):
                desc = s.get("description")
                if desc:
                    normalized_steps.append({
                        "description": desc,
                        "completed": bool(s.get("completed", False))
                    })
            else:
                # En general con TaskCreate, steps ya es lista de dicts válidos, pero convertimos seguro:
                try:
                    desc = getattr(s, "description", None)
                    comp = getattr(s, "completed", False)
                    if desc:
                        normalized_steps.append({
                            "description": desc,
                            "completed": bool(comp)
                        })
                except:
                    pass
    data["steps"] = normalized_steps

    # Verifica formato de due_date (Pydantic ya lo validó, pero repetimos por si acaso)
    try:
        datetime.strptime(data["due_date"], "%d-%m-%Y")
    except ValueError:
        raise HTTPException(status_code=400, detail="La fecha debe estar en formato dd-mm-YYYY")

    # `description`, `justification` ya validados por Pydantic con longitud, etc.

    # Guarda en Firestore
    ref = db.collection("tareas").document()
    ref.set(data)
    return {"id": ref.id, **data}

def update_task(task_id: str, task: TaskUpdate) -> dict:
    """
    Actualiza una tarea existente por ID. Recibe TaskUpdate (todos los campos requeridos sin id).
    Devuelve el documento completo actualizado (con id).
    """
    ref = db.collection("tareas").document(task_id)
    doc = ref.get()
    if not doc.exists:
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

    # Asegurar tags como lista de strings
    tags = data.get("tags")
    data["tags"] = tags if isinstance(tags, list) else []

    # Procesar steps como lista de dicts válidos
    steps = data.get("steps")
    normalized_steps = []
    if isinstance(steps, list):
        for s in steps:
            if isinstance(s, dict):
                desc = s.get("description")
                if desc:
                    normalized_steps.append({
                        "description": desc,
                        "completed": bool(s.get("completed", False))
                    })
            else:
                # Si viniera instancia Pydantic:
                try:
                    desc = getattr(s, "description", None)
                    comp = getattr(s, "completed", False)
                    if desc:
                        normalized_steps.append({
                            "description": desc,
                            "completed": bool(comp)
                        })
                except:
                    pass
    data["steps"] = normalized_steps

    # Verifica formato de due_date
    try:
        datetime.strptime(data["due_date"], "%d-%m-%Y")
    except ValueError:
        raise HTTPException(status_code=400, detail="La fecha debe estar en formato dd-mm-YYYY")

    # Actualiza en Firestore
    ref.update(data)

    # Retorna el documento completo actualizado
    updated = db.collection("tareas").document(task_id).get()
    return updated.to_dict() | {"id": updated.id}

def delete_task(task_id: str) -> dict:
    """
    Elimina la tarea; devuelve {"status":"deleted"} o lanza 404 si no existe.
    """
    ref = db.collection("tareas").document(task_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    ref.delete()
    return {"status": "deleted"}

def get_tasks_by_user(user_id: str, tag: Optional[str] = None, status: Optional[str] = None) -> List[dict]:
    """
    Obtiene tareas de un usuario, opcionalmente filtradas por etiqueta o estado.
    """
    query = db.collection("tareas").where("user_id", "==", user_id)
    if tag:
        query = query.where("tags", "array_contains", tag)
    if status:
        ns = normalize_status(status)
        query = query.where("status", "==", ns)
    return [doc.to_dict() | {"id": doc.id} for doc in query.stream()]

def get_tasks_by_status(status: Optional[str] = None) -> List[dict]:
    """
    Obtiene tareas filtradas por estado; si status es None o "Todas", devuelve todas.
    """
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


# FOCUS TIME
FOCUSCOL = db.collection("focus_times")
TASKCOL  = db.collection("tareas")


async def create_focus_time(data: FocusTimeCreate) -> Dict:
    # Leer la tarea para obtener user_id
    task_snap = TASKCOL.document(data.task_id).get()
    if not task_snap.exists:
        raise ValueError(f"Tarea con id {data.task_id} no encontrada")
    user_id = task_snap.to_dict().get("user_id")

    # Guardar nuevo FocusTime con user_id
    now = datetime.utcnow()
    payload = {
        "task_id":    data.task_id,
        "user_id":    user_id,
        "minutes":    data.minutes,
        "created_at": now,
        "updated_at": None
    }
    doc_ref = FOCUSCOL.document()
    doc_ref.set(payload)
    return {"id": doc_ref.id, **payload}


async def update_focus_time(focus_id: str, data: FocusTimeUpdate) -> Dict:
    # Verificar existencia
    doc_ref = FOCUSCOL.document(focus_id)
    snap = doc_ref.get()
    if not snap.exists:
        raise ValueError(f"FocusTime con id {focus_id} no encontrado")

    # Actualizar minutos y timestamp
    now = datetime.utcnow()
    doc_ref.update({"minutes": data.minutes, "updated_at": now})
    updated = doc_ref.get()
    return {"id": updated.id, **updated.to_dict()}


async def get_focus_by_task(task_id: str) -> List[Dict]:
    """
    Devuelve todos los FocusTime de una tarea, ordenados por fecha,
    e incluye user_id incluso si el doc antiguo no lo tenía.
    """
    docs = FOCUSCOL.where("task_id", "==", task_id).order_by("created_at").stream()
    result: List[Dict] = []

    for d in docs:
        data = d.to_dict()

        # Si falta user_id, recupéralo de la tarea
        if "user_id" not in data or data.get("user_id") is None:
            task_snap = TASKCOL.document(task_id).get()
            data["user_id"] = task_snap.to_dict().get("user_id") if task_snap.exists else None

        result.append({
            "id":          d.id,
            "task_id":     data["task_id"],
            "user_id":     data["user_id"],
            "minutes":     data["minutes"],
            "created_at":  data["created_at"],
            "updated_at":  data["updated_at"],
        })

    return result


async def get_total_focus_time_by_user(user_id: str) -> List[Dict]:
    """
    Agrupa y suma minutos de FocusTime por tarea de un usuario,
    devolviendo lista ordenada descendente.
    """
    # 1) Todas las tareas del usuario
    task_snaps = list(TASKCOL.where("user_id", "==", user_id).stream())
    if not task_snaps:
        return []

    summary: List[Dict] = []
    # 2) Para cada tarea, suma sus focus_times
    for t in task_snaps:
        tid   = t.id
        title = t.to_dict().get("title", "Sin título")
        focus_snaps = list(FOCUSCOL.where("task_id", "==", tid).stream())
        total = sum(f.to_dict().get("minutes", 0) for f in focus_snaps)
        if total > 0:
            summary.append({"task_id": tid, "task_title": title, "total_minutes": total})

    # 3) Ordenar por total_minutes desc.
    return sorted(summary, key=lambda x: x["total_minutes"], reverse=True)