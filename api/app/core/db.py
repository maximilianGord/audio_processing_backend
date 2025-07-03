from sqlmodel import Session, create_engine, select, text
from sqlalchemy.exc import OperationalError
from app import crud
from app.core.config import settings
from app.models import User, UserCreate, Conversation, ConversationCreate, Person, PersonCreate
import logging
logger = logging.getLogger(__name__)


# Create the database engine
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    pool_pre_ping=True,  # Checks connection health before use
    echo=True,  # Log SQL queries (disable in production)
)
def check_db_connection():
    """Test if the database is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
        return True
    except OperationalError as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    logger.info("Entered init_db() function")
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    from sqlmodel import SQLModel
    logger.info("Connection status: %s", check_db_connection())
    if check_db_connection():
        logger.info("Creating database tables if they do not exist...")
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables initialized (if missing)")
        user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)).first()
        if not user:
            user_in = UserCreate(
                email=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                is_superuser=True,
            )
            user = crud.create_user(session=session, user_create=user_in)
    else:
        logger.error("Could not connect to the database. Skipping table creation.")

    
