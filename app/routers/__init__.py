from fastapi import APIRouter
main_router = APIRouter()

from .auth import auth_router
main_router.include_router(auth_router)

from .todo import todo_router
main_router.include_router(todo_router)
