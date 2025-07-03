from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from pydantic_core import MultiHostUrl
from pydantic import (
    PostgresDsn
)

from dotenv import dotenv_values

config = dotenv_values(".env")
print(config.get("PORT"))
def SQLALCHEMY_DATABASE_URI() -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=config.get("USER"),
            password=config.get("PASSWORD"),
            host=config.get("HOST"),
            port=int(config.get("PORT")),
            path=config.get("DBNAME"),
        )

def test_sqlalchemy_connection():
    # Replace with your connection URI
    DATABASE_URI = str(SQLALCHEMY_DATABASE_URI())
    
    try:
        engine = create_engine(DATABASE_URI)
        with engine.connect() as conn:
            # Execute a simple query (e.g., check PostgreSQL version)
            result = conn.execute(text("SELECT version();"))
            print("✅ Connection successful! PostgreSQL version:", result.fetchone()[0])
    except SQLAlchemyError as e:
        print(f"❌ Connection failed: {e}")

# Run the test
test_sqlalchemy_connection()