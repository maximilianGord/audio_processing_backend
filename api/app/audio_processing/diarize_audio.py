import os
import logging
import torch
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PyannoteDiarizer:
    def __init__(self, hf_token: str):
        self.pipeline = None
        try:
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1", use_auth_token=hf_token
            )
            device = (
                torch.device("cuda")
                if torch.cuda.is_available()
                else (
                    torch.device("mps")
                    if torch.backends.mps.is_available()
                    else torch.device("cpu")
                )
            )
            self.pipeline.to(device)
            logger.info(f"Pipeline loaded on device: {device}")
        except Exception as e:
            logger.error(f"Error initializing Pyannote pipeline: {e}")

    def diarize(self, audio_path: str):
        """Perform speaker diarization on the given audio file."""
        if self.pipeline is None:
            logger.error("Pipeline is not initialized.")
            return None

        if not os.path.isfile(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            with ProgressHook() as hook:
                logger.info(f"Starting diarization for {audio_path}...")
                diarization = self.pipeline(audio_path, hook=hook)
                logger.info("Diarization completed.")
                return diarization
        except Exception as e:
            logger.error(f"Error during diarization: {e}")
            return None


def save_rttm(diarization, output_path):
    try:
        with open(output_path, "w") as f:
            diarization.write_rttm(f)
        logger.info(f"RTTM written to {output_path}")
    except Exception as e:
        logger.error(f"Could not write RTTM: {e}")


def print_segments(diarization):
    print("\nTranscription:\n" + "-" * 50)
    for segment, _, label in diarization.itertracks(yield_label=True):
        print(f"Speaker {label}: {segment.start:.2f}s to {segment.end:.2f}s")
    print("-" * 50)


def main():
    hf_token = (
        "***REMOVED***"  # TODO: Move to env var or config
    )
    audio_file = os.path.join("..", "conversations", "test.wav")
    output_rttm = os.path.join("..", "data", "output", "diar.rttm")

    diarizer = PyannoteDiarizer(hf_token=hf_token)
    diarization = diarizer.diarize(audio_file)

    if diarization is not None:
        print(f"Returned diarization type: {type(diarization).__name__}")
        print_segments(diarization)
        save_rttm(diarization, output_rttm)
    else:
        logger.error("Diarization failed.")


if __name__ == "__main__":
    main()
