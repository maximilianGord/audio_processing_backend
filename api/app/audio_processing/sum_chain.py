import os
import logging
from dotenv import load_dotenv
from typing import Literal, List
import pandas as pd
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.pydantic_v1 import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


# Data classes for structured output
class Person(BaseModel):
    """Information about a person."""

    name: str = Field(..., description="The full name of the person")
    person_description: str = Field(
        ...,
        description="Summarize information about the person in bulletpoints. Only include person specific information, exclude anything the person said about other topics.",
    )
    key_topics: List[str] = Field(
        ...,
        description="A list of main topics that describe the person. Each topic is returned as a key word.",
    )
    role: Literal["SPEAKER", "INTERVIEWER"] = Field(
        ...,
        description="The role of the person in the conversation. Can be either SPEAKER or INTERVIEWER. A speaker tells or explains something. An interviewer is a person who asks questions to another person. If a person is both a speaker and an interviewer, return SPEAKER.",
    )


class Conversation(BaseModel):
    """Information about a conversation."""

    summary: str = Field(
        ..., description="Summarize the following conversation to bulletpoints."
    )
    key_topics: List[str] = Field(
        ...,
        description="A list of main topics of the text. Each topic is returned as a key word.",
    )
    persons: list[Person] = Field(
        ...,
        description="A list of persons mentioned in the text. Each person is returned as a Person object.",
    )

def process_conversation(
    file_content: str
):
    """
    Reads a transcript file, parses it with an LLM, and returns the result.

    Args:
        file_path (str): Path to the transcript file.

    Returns:
        The result from the LLM, or None if an error occurs.
    """
    # Read transcript file content
    
    # LLM setup
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash",google_api_key=os.getenv("GEMINI_API_KEY"))
    structured_llm = llm.with_structured_output(Conversation)

    # Invoke LLM for structured output
    logger.info("Parsing conversation via LLM...")
    try:
        result = structured_llm.invoke(
            "Answer the following questions based on the conversation:\n\n"
            + file_content
        )
        return result
    except Exception as e:
        logger.error(f"LLM parsing failed: {e}")
        return None
    

    
def generate_follow_up_email(result, file_content, interests=None):
    """
    Generates a follow-up email suggestion using an LLM based on the conversation and user interests.

    Args:
        result: An pydantic model containing the conversation result, including persons and their roles.
        file_content (str): The conversation transcript.
        interests (list, optional): List of user interests. Defaults to a preset list.

    Returns:
        str: The generated follow-up email text, or an empty string if an error occurs.
    """
    if interests is None:
        interests = ["AI", "Machine Learning", "Data Science", "Technology", "Innovation"]

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash",google_api_key=os.getenv("GEMINI_API_KEY"))

    # Identify user (INTERVIEWER preferred)
    user = "Person A"
    interviewers = [person for person in getattr(result, "persons", []) if getattr(person, "role", "") == "INTERVIEWER"]
    if interviewers:
        user = getattr(interviewers[0], "name", "Person A")

    prompt = (
        f"Act as {user}. You want a follow up email for the following conversation: "
        f"{file_content}\nKeep in mind the following interests: {', '.join(interests)}. "
        "If you have not enough information to write the email completely, leave the missing parts blank."
    )

    # Get follow-up email suggestion
    try:
        follow_up = llm.invoke(prompt)
        follow_up_text = getattr(follow_up, "content", str(follow_up))
    except Exception as e:
        logger.error(f"Follow-up LLM invocation failed: {e}")
        follow_up_text = ""

    return follow_up_text
def export_results_from_transcript(result, file_content,follow_up_text,out_path):
    """
    exports file to an Excel file with conversation summary, key topics, and persons.

    Args:
        result: An pydantic model containing the conversation result, including persons and their roles.
        file_content (str): The conversation transcript.
        follow_up_text (str): The generated follow-up email text.

    """
    if out_path is None:
        out_path = os.path.join("..", "data", "conv_summary", "summary.xlsx")
    event = "Conference_1"
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = (
        ["Event", "Date", "Transcript", "Summary", "Key Topics"]
        + [person.name for person in result.persons]
        + ["Follow_Up_Mail"]
    )
    row = (
        [event, date_str, file_content, result.summary, result.key_topics]
        + [person.id for person in result.persons]
        + [follow_up_text]
    )
    

    # Save or update Excel file
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    try:
        if os.path.exists(out_path):
            df = pd.read_excel(out_path)
            df = pd.concat([df, pd.DataFrame([row], columns=header)], ignore_index=True)
            df.to_excel(out_path, index=False)
        else:
            df = pd.DataFrame([row], columns=header)
            df.to_excel(out_path, index=False)
        logger.info(f"Summary saved to {out_path}")
    except Exception as e:
        logger.error(f"Could not save to Excel: {e}")

def main():
    file_path = os.path.join("data", "conversation", "transcript_1.txt")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
    except Exception as e:
        logger.error(f"Could not read file: {file_path}. Error: {e}")
        return None

    result = process_conversation(file_content=file_content)

    follow_up_text = generate_follow_up_email(result=result, file_content=file_content)
    export_results_from_transcript(
        result=result,
        file_content=file_content,
        follow_up_text=follow_up_text,
        out_path=os.path.join("..", "data", "conv_summary", "summary.xlsx")
    )
    


if __name__ == "__main__":
    main()
