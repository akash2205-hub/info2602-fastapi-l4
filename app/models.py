from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from pydantic import EmailStr   #insert at top of the file

class Token(SQLModel):
    access_token: str
    token_type: str

class UserResponse(SQLModel):
    id: Optional[int]
    username:str
    email: EmailStr
    role: str

class User(SQLModel, table=False):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    password: str
    role:str = ""

class Admin(User, table=True):
    role:str = "admin"

class RegularUser(User, table=True):
    role:str = "regular_user"

    todos: list['Todo'] = Relationship(back_populates="user")

class TodoCategory(SQLModel, table=True):
    category_id: int = Field(foreign_key="category.id", primary_key=True)
    todo_id: int = Field(foreign_key="todo.id", primary_key=True)

class Category(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    user_id: int = Field(foreign_key="regularuser.id")
    text:str

    todos:list['Todo'] = Relationship(back_populates="categories", link_model=TodoCategory)

class Todo(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    user_id: int = Field(foreign_key="regularuser.id")
    text:str
    done: bool = False

    user: RegularUser = Relationship(back_populates="todos")
    categories:list['Category'] = Relationship(back_populates="todos", link_model=TodoCategory)

    def toggle(self):
        self.done = not self.done
    
    def get_cat_list(self):
        return ', '.join([category.text for category in self.categories])

class UserCreate(SQLModel):
    username:str
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)

class TodoCreate(SQLModel):
    text:str

class CategoryItem(SQLModel):
    id: int
    text: str

class TodoResponse(SQLModel):
    id: Optional[int] = Field(primary_key=True, default=None)
    text:str
    done: bool = False
    categories: List[CategoryItem] = Field(default_factory=list)

class TodoUpdate(SQLModel):
    text: Optional[str] = None
    done: Optional[bool] = None