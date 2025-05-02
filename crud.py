from fastapi import HTTPException
from models import User, Task
from database import db

# ——— USERS ———

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


# ——— TASKS ———

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
    if "status" not in task_data or not task_data["status"]:
        task_data["status"] = "Pendientes"  # Valor por defecto
    ref.set(task_data)
    return {"id": ref.id, **task_data}

def update_task(task_id: str, task: Task):
    ref = db.collection("tareas").document(task_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    task_data = task.dict()
    if "status" not in task_data or not task_data["status"]:
        task_data["status"] = "Pendientes"  # Valor por defecto
    ref.update(task_data)
    return {"status": "updated"}

def delete_task(task_id: str):
    ref = db.collection("tareas").document(task_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    ref.delete()
    return {"status": "deleted"}

def get_tasks_by_user(user_id: str):
    return [
        doc.to_dict() | {"id": doc.id}
        for doc in db.collection("tareas").where("user_id", "==", user_id).stream()
    ]