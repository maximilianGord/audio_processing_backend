import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Message
from app.models import Conversation
from app.models import Person, PersonCreate, PersonUpdate, PersonPublic, PersonsPublic
from app.crud import create_person_db, update_person_db

router = APIRouter(prefix="/persons", tags=["persons"])


@router.get("/", response_model=PersonsPublic)
def read_conversations(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve persons.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Person)
        count = session.exec(count_statement).one()
        statement = select(Person).offset(skip).limit(limit)
        persons = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Person)
            .where(Person.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Person)
            .where(Person.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        persons = session.exec(statement).all()

    return PersonsPublic(data=persons, count=count)


@router.get("/{id}", response_model=PersonPublic)
def read_person(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get person by ID.
    """
    person = session.get(Person, id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    if not current_user.is_superuser and (person.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return person


@router.post("/", response_model=PersonPublic)
def create_person(
    *, session: SessionDep, current_user: CurrentUser, person_in: PersonCreate
) -> Any:
    """
    Create new person.
    """
    return create_person_db(session, person_in, current_user.id)

@router.put("/{id}", response_model=PersonPublic)
def update_person(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    person_in: PersonUpdate,
) -> Any:
    return update_person_db(
        session=session,
        owner_id = current_user.id,
        is_superuser = current_user.is_superuser,
        id=id,
        person_in=person_in,
    )


@router.delete("/{id}")
def delete_person(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a person.
    """
    person = session.get(Person, id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    if not current_user.is_superuser and (person.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(person)
    session.commit()
    return Message(message="Person deleted successfully")

