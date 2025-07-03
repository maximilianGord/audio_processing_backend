import os
import logging
from dotenv import load_dotenv
from pathlib import Path

from pyannote.core import Segment, Annotation
from app.audio_processing.diarize_audio import PyannoteDiarizer
from app.audio_processing.transcribe_audio import transcribe_audio
from langchain_google_genai import ChatGoogleGenerativeAI

# Configuration
OUTPUT_NAME = "output_2.txt"

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpeakerAligner:
    def align(self, timestamps, diarization):
        """
        Aligns transcription segments with diarization segments.

        Args:
            timestamps (list): List of transcription segments with timestamps.
            diarization (pyannote.core.Annotation): Diarization annotation object.

        Returns:
            list: List of tuples (speaker label, start time, end time, transcription text).
        """
        speaker_transcriptions = []

        # Find the end time of the last segment in diarization
        last_diarization_end = self.get_last_segment(diarization).end

        for chunk in timestamps:
            chunk_start = chunk["start"]
            chunk_end = chunk["end"] or last_diarization_end or chunk_start
            segment_text = chunk["text"]

            best_match = self.find_best_match(diarization, chunk_start, chunk_end)
            if best_match:
                speaker = best_match[2]
                speaker_transcriptions.append(
                    (speaker, chunk_start, chunk_end, segment_text)
                )

        return self.merge_consecutive_segments(speaker_transcriptions)

    def find_best_match(self, diarization, start_time, end_time):
        best_match = None
        max_intersection = 0

        for turn, _, speaker in diarization.itertracks(yield_label=True):
            intersection_start = max(start_time, turn.start)
            intersection_end = min(end_time, turn.end)

            if intersection_start < intersection_end:
                intersection_length = intersection_end - intersection_start
                if intersection_length > max_intersection:
                    max_intersection = intersection_length
                    best_match = (turn.start, turn.end, speaker)

        return best_match

    def merge_consecutive_segments(self, segments):
        merged_segments = []
        previous = None

        for segment in segments:
            if previous is None:
                previous = segment
            elif segment[0] == previous[0]:
                # Merge consecutive segments of same speaker
                previous = (
                    previous[0],
                    previous[1],
                    segment[2],
                    previous[3] + segment[3],
                )
            else:
                merged_segments.append(previous)
                previous = segment

        if previous:
            merged_segments.append(previous)

        return merged_segments

    def get_last_segment(self, annotation):
        last_segment = None
        for segment in annotation.itersegments():
            last_segment = segment
        return last_segment



    



