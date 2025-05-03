from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models import User, Task
import crud
from database import list_collections, sample_docs
from typing import Optional

app = FastAPI(
    title="Tasko API",
    description="API para gestión de usuarios y tareas (formato de fecha: d-m-YYYY)",
    version="1.0.0",
)

# ——— CORS ———
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # o p.ej. ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ——— Ruta base ———
@app.get("/")
def root():
    return {"message": "API Tasko funcionando"}

# ——— Rutas de depuración ———
@app.get("/debug/collections")
async def debug_collections():
    return {"collections": list_collections()}

@app.get("/debug/sample")
async def debug_sample():
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
    if not user.email or not user.password:
        raise HTTPException(status_code=400, detail="Email y contraseña son requeridos.")
    return crud.login_user(user.email, user.password)


# Ejemplo de body para crear tarea (se mostrará en Swagger)
task_example = {
    "title": "Matematica",
    "description": "Entrega viernes",
    "due_date": "2-5-2025",       # formato d-m-YYYY
    "status": "Pendientes",
    "tags": ["importante", "estudio"],
    "user_id": "3sTrWtclLpAlctzEzRio"
}

# ——— Tareas ———
@app.get("/tasks")
def get_tasks(
    status: Optional[str] = Query(
        None,
        description="Filtrar por estado: Todas, Pendientes, En progreso, Completada"
    )
):
    if status:
        status = status.capitalize()
        if status not in ["Todas", "Pendientes", "En progreso", "Completada"]:
            raise HTTPException(
                status_code=400,
                detail="Estado de tarea inválido. Usa: Todas, Pendientes, En progreso o Completada."
            )
        return crud.get_tasks_by_status(status)
    return crud.get_all_tasks()

@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    return crud.get_task_by_id(task_id)

@app.get("/tasks/user/{user_id}")
def get_user_tasks(
    user_id: str,
    tag: Optional[str] = Query(None, description="Filtrar por etiqueta (tag)"),
    status: Optional[str] = Query(None, description="Filtrar por estado de tarea")
):
    return crud.get_tasks_by_user(user_id, tag, status)

@app.post(
    "/tasks",
    summary="Crear una nueva tarea",
    description="Crea una tarea. La fecha (`due_date`) debe ir en formato `d-m-YYYY`.",
)
def create_task(
    task: Task = Body(..., example=task_example)
):
    # Validación de parámetros antes de crear la tarea
    if not task.title or not task.due_date or not task.user_id:
        raise HTTPException(
            status_code=400,
            detail="Los campos 'title', 'due_date' y 'user_id' son requeridos."
        )

    return crud.create_task(task)

@app.put("/tasks/{task_id}")
def update_task(task_id: str, task: Task):
    return crud.update_task(task_id, task)

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    return crud.delete_task(task_id)


# ——— Manejo global de excepciones ———
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "message": "Ha ocurrido un error inesperado",
            "error": str(exc)
        }
    )