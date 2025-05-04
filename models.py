from pydantic import BaseModel, Field, constr, validator
from enum import Enum
from datetime import datetime
from typing import Optional, List


# Modelo para el usuario
class User(BaseModel):
    email: constr(min_length=5, max_length=100)
    password: constr(min_length=4, max_length=100)


class Status(str, Enum):
    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    COMPLETA = "Completada"

class Priority(str, Enum):
    BAJA = "Baja"
    MEDIA = "Media"
    ALTA = "Alta"

# Modelo para la tarea
class Task(BaseModel):
    title: constr(min_length=1, max_length=100) = Field(..., description="Título de la tarea")
    description: Optional[str] = Field("", description="Descripción detallada")
    due_date: constr(min_length=10, max_length=10) = Field(..., description="Fecha límite dd-mm-YYYY")
    completed: bool = Field(..., description="¿Está completada?")
    user_id: str = Field(..., description="ID del usuario dueño")
    status: Status = Field(default=Status.PENDIENTE, description="Estado de la tarea")
    priority: Priority = Field(default=Priority.MEDIA, description="Prioridad de la tarea")
    tags: List[str] = Field(default_factory=list, description="Etiquetas para filtrar/organizar")

    @validator('due_date')
    def validate_due_date_format(cls, v):
        try:
            # Verifica que el formato sea dd-mm-YYYY
            datetime.strptime(v, "%d-%m-%Y")
        except ValueError:
            raise ValueError("La fecha debe estar en el formato dd-mm-YYYY")
        return v
    
   #Modelo de notas
class Note(BaseModel):
    user_id: constr(min_length=1) = Field(..., description="ID del usuario dueño de la nota")
    title: constr(min_length=1, max_length=100) = Field(..., description="Título breve de la nota")
    texto: constr(min_length=1) = Field(..., description="Contenido de la nota")
    tags: Optional[List[constr(min_length=1)]] = Field(default_factory=list, description="Etiquetas para filtrar/organizar")
    created_at: Optional[datetime] = Field(None, description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")