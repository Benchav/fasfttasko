from fastapi import FastAPI, HTTPException, Request, Path, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import logging
import crud

from models import (
    User, Note,
    TaskCreate, TaskUpdate, TaskInDB,
    FocusTimeCreate, FocusTimeUpdate, FocusTimeInDB, FocusSummaryOut
)

from database import list_collections, sample_docs

app = FastAPI(
    title="Tasko API",
    description="API para gestión de usuarios, tareas, notas y modo enfoque",
    version="2.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Rutas básicas
@app.get("/")
def read_root():
    return {"message": "Bienvenido a Tasko API"}

@app.get("/debug/collections")
async def get_collections():
    return {"collections": list_collections()}

@app.get("/debug/sample")
async def get_sample():
    return sample_docs(["users", "tareas"])

# Simulación de tiempos
@app.get("/simular-tiempos")
async def simular_tiempos(
    sin_paginacion: float = 13.0,
    con_paginacion: float = 0.64,
    total: int = 100,
    paginados: int = 10
):
    logging.info(f"Comparativa: sin paginación {sin_paginacion}s, con paginación {con_paginacion}s")
    return {
        "mensaje": "Simulación completada",
        "tiempo_sin": f"{sin_paginacion} segundos",
        "tiempo_con": f"{con_paginacion} segundos",
        "usuarios": [{"id": i, "nombre": f"Usuario {i}"} for i in range(paginados)]
    }

# Usuarios
@app.get("/users")
def list_users():
    return {"usuarios": crud.get_all_users()}

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
        raise HTTPException(status_code=400, detail="Email y contraseña requeridos")
    return crud.login_user(user.email, user.password)

# Tareas
@app.get("/tasks", response_model=List[TaskInDB], summary="Listar todas las tareas")
async def get_tasks():
    """
    Devuelve todas las tareas.
    """
    try:
        records = crud.get_all_tasks()
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}", response_model=TaskInDB, summary="Obtener tarea por ID")
async def get_task(task_id: str = Path(..., description="ID de la tarea")):
    """
    Obtiene una tarea por su ID.
    """
    try:
        record = crud.get_task_by_id(task_id)
        return record
    except HTTPException:
        # Propaga 404 si no existe
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/user/{user_id}", response_model=List[TaskInDB], summary="Listar tareas de un usuario")
async def get_tasks_by_user(user_id: str = Path(..., description="ID del usuario")):
    """
    Obtiene las tareas asociadas a un usuario.
    """
    try:
        records = crud.get_tasks_by_user(user_id)
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks", response_model=TaskInDB, status_code=status.HTTP_201_CREATED, summary="Crear nueva tarea")
async def create_task_endpoint(payload: TaskCreate):
    """
    Crea una nueva tarea. Devuelve la tarea creada con su ID.
    """
    try:
        record = crud.create_task(payload)
        return record
    except HTTPException:
        # Propaga validaciones (400, etc.)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/tasks/{task_id}", response_model=TaskInDB, summary="Actualizar tarea completa")
async def update_task_endpoint(
    task_id: str = Path(..., description="ID de la tarea a actualizar"),
    payload: TaskUpdate = ...,
):
    """
    Actualiza todos los campos de la tarea indicada. Devuelve la tarea actualizada.
    """
    try:
        updated = crud.update_task(task_id, payload)
        return updated
    except HTTPException:
        # Propaga 404 o 400 si falla validación o no existe
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/tasks/{task_id}", status_code=status.HTTP_200_OK, summary="Eliminar tarea por ID")
async def delete_task_endpoint(task_id: str = Path(..., description="ID de la tarea a eliminar")):
    """
    Elimina la tarea indicada. Devuelve {"status": "deleted"}.
    """
    try:
        result = crud.delete_task(task_id)
        return result
    except HTTPException:
        # Propaga 404 si no existe
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Notas
@app.get("/notes")
def list_notes():
    return crud.get_all_notes()

@app.get("/notes/{note_id}")
def read_note(note_id: str):
    return crud.get_note_by_id(note_id)

@app.post("/notes")
def create_note(note: Note):
    return crud.create_note(note.user_id, note.title, note.texto, note.tags)

@app.put("/notes/{note_id}")
def update_note(note_id: str, note: Note):
    return crud.update_note(note_id, note.title, note.texto, note.tags)

@app.delete("/notes/{note_id}")
def delete_note(note_id: str):
    return crud.delete_note(note_id)





#FOCUSTIME

@app.post("/focus-times", response_model=FocusTimeInDB)
async def create_focus(payload: FocusTimeCreate):
    """
    Crea un nuevo registro de FocusTime (incluye user_id de la tarea).
    """
    try:
        rec = await crud.create_focus_time(payload)
        return FocusTimeInDB(**rec)
    except ValueError as ve:
        # Tarea no encontrada → 404
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception:
        logger.exception("Error interno al crear FocusTime")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.put("/focus-times/{focus_id}", response_model=FocusTimeInDB)
async def update_focus(focus_id: str, payload: FocusTimeUpdate):
    """
    Actualiza minutos de un FocusTime existente.
    """
    try:
        rec = await crud.update_focus_time(focus_id, payload)
        return FocusTimeInDB(**rec)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception:
        logger.exception("Error interno al actualizar FocusTime")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.get("/tasks/{task_id}/focus-times", response_model=List[FocusTimeInDB])
async def list_focus_by_task(task_id: str):
    """
    Lista todos los FocusTime de una tarea, ordenados por fecha.
    """
    recs = await crud.get_focus_by_task(task_id)
    if not recs:
        raise HTTPException(status_code=404, detail="No se encontraron registros")
    return recs


@app.get(
    "/focus-times/summary/{user_id}",
    response_model=List[FocusSummaryOut],
    summary="Resumen de FocusTime por tarea",
    description="Lista tareas de un usuario con total de minutos en foco, ordenadas."
)
async def focus_summary_by_user(user_id: str):
    """
    Resumen de minutos en FocusTime por cada tarea del usuario.
    """
    try:
        data = await crud.get_total_focus_time_by_user(user_id)
        return data
    except Exception:
        logger.exception("Error interno al obtener resumen de FocusTime")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Manejador global: convierte cualquier excepción no capturada en 500.
    """
    return JSONResponse(
        status_code=500,
        content={"message": "Error interno del servidor", "error": str(exc)}
    )