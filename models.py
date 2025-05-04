from pydantic import BaseModel, Field, constr, validator
from enum import Enum
from datetime import datetime
from typing import Optional, List

# Enumeración para los estados válidos de una tarea
class Status(str, Enum):
    PENDIENTES = "Pendientes"
    EN_PROGRESO = "En progreso"
    COMPLETA = "Completada"

# Modelo para el usuario
class User(BaseModel):
    email: constr(min_length=5, max_length=100)
    password: constr(min_length=4, max_length=100)

# Modelo para la tarea
class Task(BaseModel):
    title: constr(min_length=1, max_length=100)
    description: Optional[str] = Field(default="")
    due_date: str  # Se validará el formato con el validador
    completed: bool
    user_id: str
    status: Optional[Status] = Field(default=Status.PENDIENTES)
    tags: Optional[List[str]] = Field(default_factory=list)

    @validator('due_date')
    def validate_due_date_format(cls, v):
        try:
            # Verifica que el formato sea d-m-yyyy
            datetime.strptime(v, "%d-%m-%Y")
        except ValueError:
            raise ValueError("La fecha debe estar en el formato d-m-yyyy")
        return v
    
   #Modelo de notas
class Note(BaseModel):
    user_id: constr(min_length=1) = Field(..., description="ID del usuario dueño de la nota")
    title: constr(min_length=1, max_length=100) = Field(..., description="Título breve de la nota")
    texto: constr(min_length=1) = Field(..., description="Contenido de la nota")
    tags: Optional[List[constr(min_length=1)]] = Field(default_factory=list, description="Etiquetas para filtrar/organizar")
    created_at: Optional[datetime] = Field(None, description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")