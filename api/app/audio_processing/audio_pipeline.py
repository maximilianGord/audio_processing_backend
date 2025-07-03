import os
import sys
import logging
from dotenv import load_dotenv
from pathlib import Path

from pyannote.core import Segment, Annotation
from pydub import AudioSegment

from app.audio_processing.diarize_audio import PyannoteDiarizer
from app.audio_processing.transcribe_audio import transcribe_audio
from app.audio_processing.align import SpeakerAligner
from app.audio_processing.sum_chain import process_conversation,export_results_from_transcript,generate_follow_up_email

load_dotenv()

# Configuration
OUTPUT_NAME = "output_2.txt"

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_to_wav(input_path, output_path=None):
    """
    Converts audio files to WAV format using pydub.
    Args:

        input_path (str): Path to the input audio file.
    Returns:
        str: Path to the converted WAV file.
    """
    ext = os.path.splitext(input_path)[1].lower()

    if ext == '.wav':
        logger.info(f"File is already in WAV format: {input_path}")
        return None

    if ext == '.m4a':
        audio = AudioSegment.from_file(input_path, format='m4a')
    elif ext == '.mp4':
        audio = AudioSegment.from_file(input_path, format='mp4')
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    if output_path is None:
        output_path = os.path.splitext(input_path)[0] + '.wav'

    audio.export(output_path, format='wav')
    return  Path(input_path).with_suffix(".wav").as_posix()
    


def process(audio_path, output_name=OUTPUT_NAME):
    logger.info("Loading environment variables from .env file :"+os.getenv("GEMINI_API_KEY"))
    # Config and paths
    audio_path = convert_to_wav(audio_path)
    output_path = os.path.join("..", "data", "conv_summary", output_name)
    hf_token = os.getenv("HF_TOKEN")
    logger.info(f"Using Hugging Face token")

    # Diarization
    diarizer = PyannoteDiarizer(hf_token=hf_token)
    diarization = diarizer.diarize(audio_path)
    if diarization is None:
        logger.error("Diarization failed.")
        return
    logger.info(f"Diarization completed")
    # Transcription
    transcription = transcribe_audio(audio_path, key="segments")
    if not transcription or not isinstance(transcription, list):
        logger.error("Transcription failed or returned unexpected format.")
        return

    # Alignment
    aligner = SpeakerAligner()
    aligned_transcriptions = aligner.align(transcription, diarization)

    for speaker, start, end, text in aligned_transcriptions:
        print(f"Speaker {speaker}: {start:.2f}s to {end:.2f}s - {text}")

    # Build raw transcript for LLM
    raw_transcript = " ".join(
        [f"{segment[0]}: {segment[3]}" for segment in aligned_transcriptions]
    )

    # Summarize & Clean with LLM
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash",google_api_key=os.getenv("GEMINI_API_KEY"))
    prompt = (
        "In the following you get a dialogue. Identify the people who speak. If you can find a name of a person, "
        "use the name before the text of that person instead of the generic 'Speaker SPEAKER_00'. "
        "If you cannot find a name, try to label them by functionality (interviewer, interviewee, speaker, host, guest, etc). "
        "After that remove filler words like 'um', 'uh', 'you know', 'like' so it is easier to read, like a transcript of a podcast."
        "Also remove phrases that are not relevant to the conversation, like 'I see', 'I understand', etc."
        "Remove consecutive phrases that have the same meaning like : 'Even more, that is actually even more stressfull' will be 'that is actually even more stressfull' "
        f"The dialogue is as follows: {raw_transcript}"
    )
    final_transcription = llm.invoke(prompt)
    content = getattr(final_transcription, "content", str(final_transcription))

    # Save result
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Transcript saved to {output_path}")

    # Process conversation
    result = process_conversation(file_content=content)

    follow_up_text = generate_follow_up_email(result=result, file_content=content)
    return {
        "content": content,
        "result": result,
        "follow_up_text": follow_up_text
    }

