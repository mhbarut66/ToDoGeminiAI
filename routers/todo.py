from fastapi import Depends, Path, HTTPException, APIRouter, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse

from ..models import Base, Todo
from ..database import engine, SessionLocal
from typing import Annotated
from ..routers.auth import get_current_user
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import google.generativeai as genai
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
import markdown
from bs4 import BeautifulSoup

router = APIRouter(
    prefix="/todo",
    tags=["Todo"],
)

templates = Jinja2Templates(directory="app/templates")

class TodoRequest(BaseModel):
    title: str = Field(min_length=3, max_length=50)
    description: str = Field(min_length=3, max_length=1000)
    priority: int = Field(ge=1, le=5)
    complete: bool


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie("access_token")
    return redirect_response

@router.get("/todo-page")
async def render_todo_page(request: Request, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        todos = db.query(Todo).filter(Todo.owner_id == user.get("user_id")).all()
        return templates.TemplateResponse("todo.html", {"request": request, "todos": todos, "user": user})
    except:
        return redirect_to_login()

@router.get("/add-todo-page")
async def render_add_todo_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        return templates.TemplateResponse("add-todo.html", {"request": request, "user": user})
    except:
        return redirect_to_login()

@router.get("/edit-todo-page/{todo_id}")
async def render_edit_todo_page(request: Request, db: db_dependency, todo_id: int = Path(gt=0)):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get("user_id")).first()
        if todo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
        return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo, "user": user})
    except Exception as e:
        print(f"Error: {str(e)}")
        return redirect_to_login()

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


@router.post("/todo")
async def create_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    todo = Todo(**todo_request.model_dump(), owner_id=user.get("user_id"))
    todo.description = create_todo_with_gemini(todo.description)
    db.add(todo)
    db.commit()
    return todo


@router.put("/todo/{todo_id}")
async def update_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get("user_id")).first()
    if todo is not None:
        todo.title = todo_request.title
        todo.description = todo_request.description
        todo.priority = todo_request.priority
        todo.complete = todo_request.complete
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

def markdown_to_text(markdown_string: str):
    html = markdown.markdown(markdown_string)
    soup = BeautifulSoup(html, features="html.parser")
    text = soup.get_text()
    return text


def create_todo_with_gemini(todo_string: str):
    load_dotenv()
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    llm = ChatGoogleGenerativeAI(model="gemini-pro")
    response = llm.invoke(
        [
            HumanMessage(content="I will provide you a todo item to add my to do list. What i want you to do is to create a longer and more compherensive description of that todo item, my next message will be my todo:"),
            HumanMessage(content=todo_string),
        ]
    )
    return markdown_to_text(response.content)

if __name__ == "__main__":
    print(create_todo_with_gemini("Learn FastAPI"))