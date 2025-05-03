from fastapi import HTTPException
from typing import Optional
from models import User, Task
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

VALID_STATUSES = ["Pendientes", "En progreso", "Completada"]

def normalize_status(status: str) -> str:
    if status.lower() in ["pendiente", "pendientes"]:
        return "Pendientes"
    elif status.lower() in ["en progreso", "progreso"]:
        return "En progreso"
    elif status.lower() in ["completa", "completada"]:
        return "Completada"
    return "Pendientes"  # Por defecto

def get_all_tasks():
    return [doc.to_dict() | {"id": doc.id} for doc in db.collection("tareas").stream()]

def get_task_by_id(task_id):
    doc = db.collection("tareas").document(task_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return doc.to_dict() | {"id": doc.id}

def create_task(task: Task):
    ref = db.collection("tareas").document()
    task_data = task.dict()

    # Validar que el estado sea uno de los permitidos
    if task_data.get("status") not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Estado de tarea inválido. Usa: Pendientes, En progreso o Completada."
        )

    # Asegurar valores por defecto para 'status' y 'tags'
    task_data.setdefault("status", "Pendientes")
    task_data.setdefault("tags", [])

    # Validar que 'tags' sea una lista
    if not isinstance(task_data["tags"], list):
        task_data["tags"] = []

    # Validar el formato de la fecha antes de guardar
    try:
        task_data["due_date"] = datetime.strptime(
            task_data["due_date"], "%d-%m-%Y"
        ).strftime("%d-%m-%Y")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="La fecha debe estar en el formato d-m-yyyy"
        )

    ref.set(task_data)
    return {"id": ref.id, **task_data}

def update_task(task_id: str, task: Task):
    ref = db.collection("tareas").document(task_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    task_data = task.dict()

    # Asegurar valores por defecto para 'status' y 'tags'
    task_data.setdefault("status", "Pendientes")
    task_data.setdefault("tags", [])

    # Validar que 'tags' sea una lista
    if not isinstance(task_data["tags"], list):
        task_data["tags"] = []

    # Normalizar estado
    task_data["status"] = normalize_status(task_data["status"])

    ref.update(task_data)
    return {"status": "updated"}

def delete_task(task_id: str):
    ref = db.collection("tareas").document(task_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    ref.delete()
    return {"status": "deleted"}

def get_tasks_by_user(user_id: str, tag: Optional[str] = None, status: Optional[str] = None):
    query = db.collection("tareas").where("user_id", "==", user_id)

    if tag:
        query = query.where("tags", "array_contains", tag)

    if status:
        status = normalize_status(status)
        query = query.where("status", "==", status)

    return [
        doc.to_dict() | {"id": doc.id}
        for doc in query.stream()
    ]

def get_tasks_by_status(status: Optional[str] = None):
    tasks_ref = db.collection("tareas")

    if status and status != "Todas":
        status = normalize_status(status)
        tasks_ref = tasks_ref.where("status", "==", status)

    return [doc.to_dict() | {"id": doc.id} for doc in tasks_ref.stream()]