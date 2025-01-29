from fastapi import FastAPI, Depends, Path, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status

from models import Base, Todo
from database import engine, SessionLocal
from typing import Annotated

app = FastAPI()

Base.metadata.create_all(bind=engine)


class TodoRequest(BaseModel):
    title: str = Field(min_length=3, max_length=50)
    describe: str = Field(min_length=3, max_length=1000)
    priority: int = Field(ge=1, le=5)
    completed: bool



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/read_all")
async def read_all(db: db_dependency):
    return db.query(Todo).all()

@app.get("/get_by_id/{todo_id}")
async def read_by_id(db: db_dependency, todo_id: int = Path(gt=0)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is not None:
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")


@app.post("/create_todo")
async def create(db: db_dependency, todo_request: TodoRequest):
    todo = Todo(**todo_request.model_dump())
    db.add(todo)
    db.commit()


@app.put("/update_todo/{todo_id}")
async def update_todo(db: db_dependency, todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is not None:
        todo.title = todo_request.title
        todo.describe = todo_request.describe
        todo.priority = todo_request.priority
        todo.completed = todo_request.completed
        db.commit()
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

@app.delete("/delete_todo/{todo_id}")
async def delete_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is not None:
        db.delete(todo)
        db.commit()
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")