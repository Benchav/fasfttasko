from pydantic import BaseModel, Field, constr
from enum import Enum
from typing import Optional, List

# Enumeración para los estados válidos de una tarea
class Status(str, Enum):
    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    COMPLETADA = "Completada"

# Modelo para el usuario
class User(BaseModel):
    email: constr(min_length=5, max_length=100)
    password: constr(min_length=4, max_length=100)

# Modelo para la tarea
class Task(BaseModel):
    title: constr(min_length=1, max_length=100)
    description: Optional[str] = Field(default="")
    due_date: constr(min_length=10, max_length=10)  # "YYYY-MM-DD"
    completed: bool
    user_id: str
    status: Optional[Status] = Field(default=Status.PENDIENTE)
    tags: Optional[List[str]] = Field(default_factory=list)