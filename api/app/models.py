import uuid

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    
    items: "Item" = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "delete"}
    )
    # One-to-many with Conversation
    conversations: List["Conversation"] = Relationship(back_populates="owner")
    
    # One-to-many with Person
    persons: List["Person"] = Relationship(back_populates="owner")

# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int




#Conversations 

class Participation(SQLModel, table=True):
    person_id: uuid.UUID = Field(foreign_key="person.id", primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="conversation.id", primary_key=True)

class Conversation(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner:User = Relationship(back_populates="conversations")
    day: str | None = Field(default=None, max_length=255)  
    event: str | None = Field(default=None, max_length=255)  
    transcript: str | None = Field(default=None)  
    summary: str | None = Field(default=None)  
    key_topics: Optional[List[str]] = Field(default=None,sa_column=Column(JSONB))    
    persons: List["Person"] = Relationship(back_populates="conversations", link_model=Participation)
    follow_up_text: str | None = Field(default=None)

# Properties to receive on item creation
class ConversationCreate(SQLModel):
    day: Optional[str] = Field(default=None, max_length=255)
    event: Optional[str] = Field(default=None, max_length=255)
    transcript: Optional[str] = None
    summary: Optional[str] = None
    key_topics: Optional[List[str]] = None
    person_ids: Optional[List[uuid.UUID]] = None
    follow_up_text: Optional[str] = None

class ConversationUpdate(SQLModel):
    day: Optional[str] = Field(default=None, max_length=255)
    event: Optional[str] = Field(default=None, max_length=255)
    transcript: Optional[str] = None
    summary: Optional[str] = None
    key_topics: Optional[List[str]] = None
    person_ids: Optional[List[uuid.UUID]] = None
    follow_up_text: Optional[str] = None

class ConversationPublic(SQLModel):
    id: uuid.UUID
    owner_id: uuid.UUID


class ConversationsPublic(SQLModel):
    data: list[ConversationPublic]
    count: int


class Person(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User  = Relationship(back_populates="persons")
    name: str | None = Field(default=None,max_length = 255)  # type: ignore
    person_description: str | None = Field(default=None)  # type: ignore
    key_topics: Optional[List[str]] = Field(default=None,sa_column=Column(JSONB))    
    links: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSONB)  # use JSON for SQLite or other DBs
    )
    conversations: List["Conversation"] =  Relationship(back_populates="persons", link_model=Participation)


# Properties to receive on item creation
class PersonCreate(SQLModel):
    name: Optional[str] = Field(default=None, max_length=255)  # string with max length
    person_description: Optional[str] = Field(default=None)  # optional string
    key_topics: Optional[List[str]] = Field(default=None)  # list of strings, no max_length here
    links: Optional[List[str]] = Field(default=None)  # list of strings, no max_length here
    conversation_ids: Optional[List[uuid.UUID]] = None  # list of UUIDs for relation references


class PersonUpdate(SQLModel):
    transcript: Optional[str] = Field(default=None)  # optional string
    summary: Optional[str] = Field(default=None)  # optional string
    key_topics: Optional[List[str]] = Field(default=None)  # list of strings, match model
    links: Optional[List[str]] = Field(default=None)  # list of strings
    conversation_ids: Optional[List[uuid.UUID]] = None  # reference by IDs for update

# Properties to receive on item update
class PersonPublic(SQLModel):
    id: uuid.UUID
    owner_id: uuid.UUID


class PersonsPublic(SQLModel):
    data: list[PersonPublic]
    count: int




# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)

if TYPE_CHECKING:
    from .conversation import Conversation
    from .person import Person
    from .item import Item