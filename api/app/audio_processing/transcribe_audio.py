import os
import logging
import whisper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def transcribe_audio(audio_path: str, model_name: str = "tiny", key: str = "text"):
    """
    Transcribe an audio file using Whisper.

    Args:
        audio_path (str): Path to the audio file.
        model_name (str): Whisper model to use (default "tiny").
        key (str): Key to extract from the result ("text" or "segments").

    Returns:
        str | list: Transcribed text or list of segments.
    """
    try:
        # Check if file exists
        if not os.path.isfile(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Loading Whisper model '{model_name}'...")
        model = whisper.load_model(model_name)

        logger.info(f"Transcribing {audio_path}...")
        result = model.transcribe(audio_path)

        if key not in result:
            logger.error(f"Key '{key}' not found in transcription result.")
            raise KeyError(f"Key '{key}' not found in transcription result.")
        return result[key]

    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        return None


def main():
    audio_file = "test.m4a"
    path = os.path.join("..", "conversations", audio_file)

    logger.info("Starting transcription...")
    transcription = transcribe_audio(path)

    print("\nTranscription:")
    print("-" * 50)
    if transcription:
        print(transcription)
    else:
        print("Transcription failed. See logs for details.")
    print("-" * 50)


if __name__ == "__main__":
    main()
