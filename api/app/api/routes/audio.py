import logging
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File
from sqlmodel import Session, select, func

from app.core.config import settings
from app.api.deps import CurrentUser, SessionDep
from app.models import Message, User
from app.models import Conversation, ConversationCreate
from app.models import Person, PersonCreate
from app.audio_processing.audio_pipeline import process
from app.crud import create_conversation_db, create_person_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audio", tags=["audio"])
# For development purposes, I removed the need for authentication in this example.
@router.post("/upload")
async def upload_audio(
    session: SessionDep,
    #current_user: CurrentUser,  # Assuming a dummy user ID for development purposes, change later id = current_user --> id = current_user.id
    file: UploadFile = File(...)
):
    # Example logic: save file, log user, etc.
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:  # 50 MB limit
        raise HTTPException(status_code=413, detail="File is too large.")
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)  # ✅ Ensure directory exists
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(contents)
    # You can use session and current_user here as needed
    processed_result = process(f"uploads/{file.filename}")
    if not processed_result:
        raise HTTPException(status_code=500, detail="Audio processing failed.")
    #create conversation from processed result

    person_ids = [str(uuid.uuid4()) for person in processed_result["result"].persons]
    conversation_id = str(uuid.uuid4())
    logger.info(f"Creating db")
    #create persons from processed result
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()
    logger.info(f"User count: {count}")
    current_user_id = session.exec(select(User.id).where(User.email == settings.FIRST_SUPERUSER)).first()
    logger.info(f"Current user id: {current_user_id}")

    persons = []
    for person,id in list(zip(processed_result["result"].persons,person_ids)):
        person_in = PersonCreate(
            id=id,
            owner_id=current_user_id,
            name=person.name,
            person_description=person.person_description,
            key_topics=person.key_topics,
            conversation_ids=[conversation_id],
        )
        persons.append( create_person_db(session=session,
                                    person_in = person_in,
                                    owner_id = current_user_id
                                    ))  

    conversation_in = ConversationCreate(
        title=file.filename,
        description="Audio file processed",
        id = conversation_id,  # Generate a unique ID for the conversation 
        owner_id=current_user_id,
        person_ids=person_ids,
        day = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        event = "Audio Processing Event",
        transcript=processed_result["content"],
        summary=processed_result["result"].summary,
        key_topics=processed_result["result"].key_topics,
        follow_up_text=processed_result["follow_up_text"]
    )
    conversation = create_conversation_db(session = session,
                                            conversation_in = conversation_in,
                                            owner_id = current_user_id
                                            )                                            

    return {
    "filename": file.filename,
    "message": "Upload successful!",
    "conversation_id": conversation.id,
    "person_ids": [person.id for person in persons],
    "follow_up_text": conversation.follow_up_text
}