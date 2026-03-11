from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from app.database import SessionDep
from app.models import *
from app.auth import encrypt_password, verify_password, create_access_token, AuthDep
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import status

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