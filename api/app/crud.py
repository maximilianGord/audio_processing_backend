import uuid
from typing import Any

from sqlmodel import Session, select

from fastapi import HTTPException

from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate
from app.models import Conversation, ConversationCreate, ConversationUpdate
from app.models import Person, PersonCreate, PersonUpdate



def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

def create_conversation_db(*, session: Session, conversation_in: ConversationCreate, owner_id: uuid.UUID) -> Conversation:
    db_conversation = Conversation.model_validate(conversation_in, update={"owner_id": owner_id})

    # Optionally handle persons if person_ids are provided
    if conversation_in.person_ids:
        persons = session.exec(
            select(Person).where(Person.id.in_(conversation_in.person_ids))
        ).all()
        db_conversation.persons = persons

    session.add(db_conversation)
    session.commit()
    session.refresh(db_conversation)
    return db_conversation

def update_conversation_db(
    *, session: Session,
    owner_id: uuid.UUID,
    is_superuser: bool,
    id: uuid.UUID,
    conversation_in: ConversationUpdate,
) -> Conversation:
    """
    Update an conversation.
    """
    conversation = session.get(Conversation, id)
    if not conversation:
        raise HTTPException(status_code=404, detail="conversation not found")
    if not is_superuser and (conversation.owner_id != owner_id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = conversation_in.model_dump(exclude_unset=True)
    conversation.sqlmodel_update(update_dict)
     # Handle persons if person_ids are provided
    if conversation_in.person_ids is not None:
        if conversation_in.person_ids:
            persons = session.exec(
                select(Person).where(Person.id.in_(conversation_in.person_ids))
            ).all()
            conversation.persons = persons
        else:
            # If an empty list is provided, clear all persons
            conversation.persons = []

    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation

def create_person_db(*, session: Session, person_in: PersonCreate, owner_id: uuid.UUID) -> Person:
     
    person = Person.model_validate(person_in, update={"owner_id": owner_id})

    # Optionally handle persons if person_ids are provided
    if person_in.conversation_ids:
        conversations = session.exec(
            select(Conversation).where(Conversation.id.in_(person_in.conversation_ids))
        ).all()
        person.conversations = conversations

    session.add(person)
    session.commit()
    session.refresh(person)
    return person

def update_person_db(
    *,
    session: Session,
    owner_id: uuid.UUID,
    is_superuser: bool,
    id: uuid.UUID,
    person_in: PersonUpdate,
) -> Any:
    """
    Update an person.
    """
    person = session.get(Person, id)
    if not person:
        raise HTTPException(status_code=404, detail="person not found")
    if not is_superuser and (person.owner_id != owner_id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = person_in.model_dump(exclude_unset=True)
    person.sqlmodel_update(update_dict)
     # Handle persons if person_ids are provided
    if person_in.conversation_ids is not None:
        if person_in.conversation_ids:
            conversations = session.exec(
                select(Conversation).where(Conversation.id.in_(person_in.conversation_ids))
            ).all()
            person.conversations = conversations
        else:
            # If an empty list is provided, clear all persons
            person.conversations = []

    session.add(person)
    session.commit()
    session.refresh(person)
    return person