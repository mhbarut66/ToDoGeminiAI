from fastapi import Depends, Path, HTTPException, APIRouter
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
from models import Base, Todo
from database import engine, SessionLocal
from typing import Annotated
from routers.auth import get_current_user

router = APIRouter(
    prefix="/todo",
    tags=["Todo"],
)


class TodoRequest(BaseModel):
    title: str = Field(min_length=3, max_length=50)
    description: str = Field(min_length=3, max_length=1000)
    priority: int = Field(ge=1, le=5)
    completed: bool


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/")
async def get_all(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return db.query(Todo).filter(Todo.owner_id == user.get("user_id")).all()


@router.get("/todo/{todo_id}")
async def get_by_id(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get("user_id")).first()
    if todo is not None:
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")


@router.post("/create")
async def create(user: user_dependency, db: db_dependency, todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    todo = Todo(**todo_request.model_dump(), owner_id=user.get("user_id"))
    db.add(todo)
    db.commit()


@router.put("/todo/{todo_id}")
async def update_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get("user_id")).first()
    if todo is not None:
        todo.title = todo_request.title
        todo.description = todo_request.description
        todo.priority = todo_request.priority
        todo.completed = todo_request.completed
        db.commit()
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")


@router.delete("/todo/{todo_id}")
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get("user_id")).first()
    if todo is not None:
        db.delete(todo)
        db.commit()
    return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
