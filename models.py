from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List

# Enumeración para los estados válidos de una tarea
class Status(str, Enum):
    PENDIENTES = "Pendientes"
    EN_PROGRESO = "En progreso"
    COMPLETA = "Completada"

# Modelo para el usuario
class User(BaseModel):
    email: str
    password: str

# Modelo para la tarea
class Task(BaseModel):
    title: str
    description: str
    due_date: str
    completed: bool
    user_id: str
    status: Optional[Status] = Field(default=Status.PENDIENTES)
    tags: Optional[List[str]] = Field(default_factory=list)