from youtube_transcript_api import YouTubeTranscriptApi
import sys
import re


def extract_video_id(url: str) -> str:
    """Extract the video ID from a YouTube URL."""
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    if len(url) == 11:
        return url
    raise ValueError("Invalid YouTube URL or video ID.")


def get_transcript(video_id: str):
    """Fetch the transcript for the given video ID."""
    try:
        return YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/get_youtube_transcript.py <YouTube URL or Video ID>")
        sys.exit(1)

    url = sys.argv[1]
    try:
        video_id = extract_video_id(url)
        transcript = get_transcript(video_id)
        if transcript:
            for entry in transcript:
                print(f"{entry['start']:.2f}s: {entry['text']}")
        else:
            print("Transcript not available.")
    except Exception as e:
        print(f"Error: {e}")
