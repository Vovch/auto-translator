import ffmpeg
import argparse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def extract_audio(input_video, output_audio=None):
    """
    Extract audio from a video file using ffmpeg
    
    Args:
        input_video (str): Path to input video file
        output_audio (str): Path to output audio file (optional)
    """
    if not os.path.exists(input_video):
        raise FileNotFoundError(f"Input video file not found: {input_video}")
    
    # If output path is not specified, create one based on input filename
    if output_audio is None:
        base_name = os.path.splitext(input_video)[0]
        output_audio = f"{base_name}_audio.mp3"
    
    try:
        # Extract audio using ffmpeg with codec from env
        audio_codec = os.getenv('AUDIO_CODEC', 'libmp3lame')
        stream = ffmpeg.input(input_video)
        stream = ffmpeg.output(stream, output_audio, acodec=audio_codec)
        ffmpeg.run(stream, overwrite_output=True)
        print(f"Audio successfully extracted to: {output_audio}")
        return output_audio
    except ffmpeg.Error as e:
        print(f"An error occurred: {e.stderr.decode()}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Extract audio from video file')
    parser.add_argument('input', help='Input video file path')
    parser.add_argument('-o', '--output', help='Output audio file path (optional)')
    
    args = parser.parse_args()
    output_path = extract_audio(args.input, args.output)
    if output_path:
        print(f"Output path: {output_path}")

if __name__ == "__main__":
    main()
