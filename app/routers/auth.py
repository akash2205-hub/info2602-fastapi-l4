from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from app.database import SessionDep
from app.models import *
from app.auth import encrypt_password, verify_password, create_access_token, AuthDep
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import status
from sqlalchemy.orm import selectinload

auth_router = APIRouter(tags=["Authentication"])

@auth_router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDep
) -> Token:
    user = db.exec(select(RegularUser).where(RegularUser.username == form_data.username)).one_or_none()
    if not user or not verify_password(plaintext_password=form_data.password, encrypted_password=user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": f"{user.id}", "role": user.role},)

    return Token(access_token=access_token, token_type="bearer")

@auth_router.get("/identify", response_model=UserResponse)
def get_user_by_id(db: SessionDep, user:AuthDep):
    return user

@auth_router.post('/signup', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup_user(user_data: UserCreate, db:SessionDep):
  try:
    new_user = RegularUser(
        username=user_data.username, 
        email=user_data.email, 
        password=encrypt_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    return new_user
  except Exception:
    db.rollback()
    raise HTTPException(
                status_code=400,
                detail="Username or email already exists",
                headers={"WWW-Authenticate": "Bearer"},
            )
  
@auth_router.post('/category', response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(db:SessionDep, user:AuthDep, category_data:TodoCreate):
    category = Category(text=category_data.text, user_id=user.id)
    try:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while creating a category",
        )
    
@auth_router.post('/todo/{todo_id}/category/{cat_id}')
def add_category_to_todo(todo_id:int, cat_id:int, db:SessionDep, user:AuthDep):
    todo = db.exec(select(Todo).where(Todo.id==todo_id, Todo.user_id==user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    category = db.exec(select(Category).where(Category.id==cat_id, Category.user_id==user.id)).one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    existing = db.exec(select(TodoCategory).where(TodoCategory.todo_id==todo_id, TodoCategory.category_id==cat_id)).one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category already assigned to this todo",
        )
    
    todo_category = TodoCategory(todo_id=todo_id, category_id=cat_id)
    try:
        db.add(todo_category)
        db.commit()
        return {"message": "Category successfully added to todo"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while adding category to todo",
        )
    
@auth_router.delete('/todo/{todo_id}/category/{cat_id}')
def remove_category_from_todo(todo_id:int, cat_id:int, db:SessionDep, user:AuthDep):
    todo = db.exec(select(Todo).where(Todo.id==todo_id, Todo.user_id==user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    category = db.exec(select(Category).where(Category.id==cat_id, Category.user_id==user.id)).one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    todo_category = db.exec(select(TodoCategory).where(TodoCategory.todo_id==todo_id, TodoCategory.category_id==cat_id)).one_or_none()
    if not todo_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not assigned to this todo",
        )
    
    try:
        db.delete(todo_category)
        db.commit()
        return {"message": "Category successfully removed from todo"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while removing category from todo",
        )
    
@auth_router.get('/category/{cat_id}/todos', response_model=List[TodoResponse])
def get_todos_for_category(cat_id:int, db:SessionDep, user:AuthDep):
    category = db.exec(
        select(Category)
        .where(Category.id==cat_id, Category.user_id==user.id)
        .options(selectinload(Category.todos))
    ).one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return category.todos