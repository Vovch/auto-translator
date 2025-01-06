import argparse
from extract_audio import extract_audio
from transcribe_audio import transcribe_audio

def process_video(input_video, output_audio=None):
    """
    Process a video file by extracting audio and transcribing it
    
    Args:
        input_video (str): Path to input video file
        output_audio (str): Path to output audio file (optional)
    """
    # Step 1: Extract audio
    audio_file = extract_audio(input_video, output_audio)
    if not audio_file:
        return
    
    # Step 2: Transcribe audio
    try:
        transcript_file = transcribe_audio(audio_file)
        print(f"Video processing completed successfully!")
    except Exception as e:
        print(f"An error occurred during transcription: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Extract audio from video and transcribe it')
    parser.add_argument('input', help='Input video file path')
    parser.add_argument('-o', '--output', help='Output audio file path (optional)')
    
    args = parser.parse_args()
    process_video(args.input, args.output)

if __name__ == "__main__":
    main()
