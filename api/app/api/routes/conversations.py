import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select
from app.crud import create_conversation_db, update_conversation_db


from app.api.deps import CurrentUser, SessionDep
from app.models import Message
from app.models import Conversation,ConversationCreate,ConversationUpdate,ConversationPublic,ConversationsPublic
from app.models import Person

router = APIRouter(prefix="/conversation", tags=["conversations"])


@router.get("/", response_model=ConversationsPublic)
def read_conversations(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve conversations.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Conversation)
        count = session.exec(count_statement).one()
        statement = select(Conversation).offset(skip).limit(limit)
        conversations = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Conversation)
            .where(Conversation.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        conversations = session.exec(statement).all()

    return ConversationsPublic(data=conversations, count=count)


@router.get("/{id}", response_model=ConversationPublic)
def read_conversation(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get Conversation by ID.
    """
    conversation = session.get(Conversation, id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not current_user.is_superuser and (conversation.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return conversation


@router.post("/", response_model=ConversationPublic)
def create_conversation(
    *, session: SessionDep, current_user: CurrentUser, conversation_in: ConversationCreate
) -> Any:
    """
    Create new conversation.
    """
    return create_conversation_db(session, conversation_in, current_user.id)

@router.put("/{id}", response_model=ConversationPublic)
def update_conversation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    conversation_in: ConversationUpdate,
) -> Any:
    """
    Update an conversation.
    """
    return update_conversation_db(
        session=session,
        owner_id=current_user.id,
        is_superuser=current_user.is_superuser,
        id=id, 
        conversation_in=conversation_in)


@router.delete("/{id}")
def delete_conversation(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a conversation.
    """
    conversation = session.get(Conversation, id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not current_user.is_superuser and (conversation.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(conversation)
    session.commit()
    return Message(message="Conversation deleted successfully")

