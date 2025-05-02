from pydantic import BaseModel

class User(BaseModel):
    email: str
    password: str

class Task(BaseModel):
    title: str
    description: str
    due_date: str
    completed: bool
    user_id: str