from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models import User, Task, Note
import crud
from database import list_collections, sample_docs
from typing import Optional, List


task_example = {
    "title": "Estudiar matemáticas",
    "description": "Repasar álgebra y geometría",
    "due_date": "05-05-2025",
    "completed": False,
    "user_id": "b0ZngTJpjvDhd9adfb97",
    "status": "Pendiente",
    "priority": "Media",
    "tags": ["estudio", "importante"]
}

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
        description="Filtrar por estado: Todas, Pendiente, En progreso, Completa"
    )
):
    if status:
        status = status.capitalize()
        if status not in ["Todas", "Pendiente", "En progreso", "Completa"]:
            raise HTTPException(
                status_code=400,
                detail="Estado de tarea inválido. Usa: Todas, Pendiente, En progreso o Completa."
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
    description=(
        "Crea una tarea. La fecha (`due_date`) debe ir en formato `dd-mm-YYYY`. "
        "Opcionalmente, se puede enviar `justification` en caso de que la tarea no se cumpla."
    ),
)
def create_task(
    task: Task = Body(..., example={
        # Ejemplo mínimo:
        "title": "Comprar repuestos",
        "description": "Ir a la tienda de autos a comprar pastillas de freno",
        "due_date": "10-06-2025",
        "user_id": "usuario123",
        "status": "Pendiente",
        "priority": "Media",
        "tags": ["repuestos", "auto"],
        "steps": [{"description": "Llamar a la tienda", "completed": False}],
        "justification": ""  # Opcional: motivo si no se completa
    })
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


# ——— Notes ———

@app.get("/notes")
def list_notes():
    return crud.get_all_notes()

@app.get("/notes/{note_id}")
def read_note(note_id: str):
    return crud.get_note_by_id(note_id)

@app.post("/notes")
def create_note_endpoint(note: Note):
    # Nota: crud.create_note ahora debe aceptar user_id, title, texto y tags
    return crud.create_note(
        user_id=note.user_id,
        title=note.title,
        texto=note.texto,
        tags=note.tags
    )

@app.put("/notes/{note_id}")
def update_note_endpoint(note_id: str, note: Note):
    return crud.update_note(
        note_id=note_id,
        title=note.title,
        texto=note.texto,
        tags=note.tags
    )

@app.delete("/notes/{note_id}")
def delete_note_endpoint(note_id: str):
    return crud.delete_note(note_id)


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


