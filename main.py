from fastapi import FastAPI, HTTPException
from models import User, Task
import crud
from database import list_collections, sample_docs
from typing import Optional

app = FastAPI()

# ——— Ruta base ———
@app.get("/")
def root():
    return {"message": "API Tasko funcionando"}

# ——— Rutas de depuración ———
@app.get("/debug/collections")
async def debug_collections():
    """
    Lista todas las colecciones que ve Firestore según tu Service Account.
    """
    return {"collections": list_collections()}

@app.get("/debug/sample")
async def debug_sample():
    """
    Devuelve un documento de ejemplo de tus colecciones 'users' y 'tareas'.
    """
    return sample_docs(["users", "tareas"])

# ——— Usuarios ———
@app.get("/users")
def get_users():
    return crud.get_all_users()

@app.get("/users/{user_id}")
def get_user(user_id: str):
    return crud.get_user_by_id(user_id)

@app.post("/users")
def create_user(user: User):
    return crud.create_user(user)

@app.put("/users/{user_id}")
def update_user(user_id: str, user: User):
    return crud.update_user(user_id, user)

@app.delete("/users/{user_id}")
def delete_user(user_id: str):
    return crud.delete_user(user_id)

@app.post("/login")
def login(user: User):
    return crud.login_user(user.email, user.password)

# ——— Tareas ———
@app.get("/tasks")
def get_tasks(status: Optional[str] = None):
    """
    Obtiene todas las tareas, opcionalmente filtradas por su status.
    Valores de 'status' permitidos: Todas, Pendientes, En progreso, Completada
    """
    if status:
        status = status.capitalize()  # Asegura que el valor de status esté correctamente capitalizado
        if status not in ["Todas", "Pendientes", "En progreso", "Completada"]:
            raise HTTPException(status_code=400, detail="Estado de tarea inválido. Usa 'Todas', 'Pendientes', 'En progreso' o 'Completada'.")
        return [task for task in crud.get_all_tasks() if task["status"] == status or status == "Todas"]
    return crud.get_all_tasks()

@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    return crud.get_task_by_id(task_id)

@app.get("/tasks/user/{user_id}")
def get_user_tasks(user_id: str):
    return crud.get_tasks_by_user(user_id)

@app.post("/tasks")
def create_task(task: Task):
    return crud.create_task(task)

@app.put("/tasks/{task_id}")
def update_task(task_id: str, task: Task):
    return crud.update_task(task_id, task)

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    return crud.delete_task(task_id)