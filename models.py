from pydantic import BaseModel, Field, constr, validator
from enum import Enum
from datetime import datetime
from typing import Optional, List


# Modelo para el usuario
class User(BaseModel):
    email: constr(min_length=5, max_length=100)
    password: constr(min_length=4, max_length=100)



# Enums:
class Status(str, Enum):
    PENDIENTE   = "Pendiente"
    EN_PROGRESO = "En progreso"
    COMPLETA    = "Completada"

class Priority(str, Enum):
    BAJA  = "Baja"
    MEDIA = "Media"
    ALTA  = "Alta"

# Submodelo Step:
class Step(BaseModel):
    description: constr(min_length=1, max_length=200) = Field(
        ..., description="Descripción del paso"
    )
    completed: bool = Field(
        False, description="Indica si el paso está completado"
    )

# Modelo base con campos comunes (sin id):
class TaskBase(BaseModel):
    title: constr(min_length=1, max_length=100) = Field(
        ..., description="Título de la tarea"
    )
    description: Optional[str] = Field(
        "", description="Descripción detallada de la tarea"
    )
    due_date: constr(min_length=10, max_length=10) = Field(
        ..., description="Fecha límite en formato dd-mm-YYYY"
    )
    completed: bool = Field(
        False, description="Indica si la tarea está completada"
    )
    user_id: str = Field(
        ..., description="ID del usuario dueño de la tarea"
    )
    status: Status = Field(
        default=Status.PENDIENTE, description="Estado global de la tarea"
    )
    priority: Priority = Field(
        default=Priority.MEDIA, description="Prioridad de la tarea"
    )
    tags: List[str] = Field(
        default_factory=list, description="Etiquetas para filtrar/organizar"
    )
    steps: List[Step] = Field(
        default_factory=list, description="Lista de pasos o subtareas"
    )
    justification: Optional[constr(max_length=500)] = Field(
        "", description="Justificación de por qué no se cumplió la tarea (máx. 500 caracteres)"
    )

    @validator('due_date')
    def validate_due_date_format(cls, v):
        try:
            datetime.strptime(v, "%d-%m-%Y")
        except ValueError:
            raise ValueError("La fecha debe estar en el formato dd-mm-YYYY")
        return v

# Modelo para creación (idéntico a TaskBase, ya que todos los campos required salvo defaults):
class TaskCreate(TaskBase):
    pass

# Modelo para actualización vía PUT (requiere enviar todos los campos excepto id, igual a TaskBase)
class TaskUpdate(TaskBase):
    pass

# Si quisieras PATCH (solo campos opcionales), podrías:
class TaskPartialUpdate(BaseModel):
    title: Optional[constr(min_length=1, max_length=100)]
    description: Optional[str]
    due_date: Optional[constr(min_length=10, max_length=10)]
    completed: Optional[bool]
    user_id: Optional[str]
    status: Optional[Status]
    priority: Optional[Priority]
    tags: Optional[List[str]]
    steps: Optional[List[Step]]
    justification: Optional[constr(max_length=500)]

    @validator('due_date')
    def validate_due_date_format_optional(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, "%d-%m-%Y")
        except ValueError:
            raise ValueError("La fecha debe estar en el formato dd-mm-YYYY")
        return v

# Modelo de respuesta, incluye id y timestamps si quieres:
class TaskInDB(TaskBase):
    id: str = Field(..., description="ID de la tarea")
    # Podrías incluir created_at, updated_at si los guardas:
    # created_at: datetime
    # updated_at: Optional[datetime]

    class Config:
        orm_mode = True


    
   #Modelo de notas
class Note(BaseModel):
    user_id: constr(min_length=1) = Field(..., description="ID del usuario dueño de la nota")
    title: constr(min_length=1, max_length=100) = Field(..., description="Título breve de la nota")
    texto: constr(min_length=1) = Field(..., description="Contenido de la nota")
    tags: Optional[List[constr(min_length=1)]] = Field(default_factory=list, description="Etiquetas para filtrar/organizar")
    created_at: Optional[datetime] = Field(None, description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")


# --- Modelos existentes ---

class FocusTimeCreate(BaseModel):
    task_id: str = Field(..., description="ID de la tarea asociada")
    minutes: int = Field(..., gt=0, description="Minutos que el usuario pasó en Focus Mode")

class FocusTimeUpdate(BaseModel):
    minutes: int = Field(..., gt=0, description="Minutos actualizados acumulados")

class FocusTimeInDB(FocusTimeCreate):
    id: str = Field(..., description="ID generado del registro de FocusTime")
    user_id: str = Field(..., description="ID del usuario dueño de la tarea")
    created_at: datetime = Field(..., description="Fecha de creación del registro")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")

    class Config:
        orm_mode = True  # o from_attributes en Pydantic v2

# --- Nuevo schema para el resumen ---

class FocusSummaryOut(BaseModel):
    task_id: str
    task_title: str
    total_minutes: int

    class Config:
        orm_mode = True  # o from_attributes