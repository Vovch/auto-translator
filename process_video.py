import argparse
import os
from extract_audio import extract_audio
from transcribe_audio import transcribe_audio
from translate_subtitles import translate_srt

def process_video(input_video, output_audio=None, target_lang="en"):
    """
    Process a video file by extracting audio, transcribing it, and translating the subtitles
    
    Args:
        input_video (str): Path to input video file
        output_audio (str): Path to output audio file (optional)
        target_lang (str): Target language for translation (default: en)
    """
    # Step 1: Extract audio
    audio_file = extract_audio(input_video, output_audio)
    if not audio_file:
        return
    
    # Step 2: Transcribe audio
    try:
        transcript_file = transcribe_audio(audio_file)
        if not transcript_file:
            return
        
        # Step 3: Translate subtitles
        if target_lang != "en":  # Only translate if target language is not English
            base_name = os.path.splitext(transcript_file)[0]
            translated_file = f"{base_name}_{target_lang}.srt"
            translate_srt(transcript_file, translated_file, "auto", target_lang)
            print(f"Video processing and translation completed successfully!")
        else:
            print(f"Video processing completed successfully!")
            
    except Exception as e:
        print(f"An error occurred during processing: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Extract audio from video, transcribe it, and translate subtitles')
    parser.add_argument('input', help='Input video file path')
    parser.add_argument('-o', '--output', help='Output audio file path (optional)')
    parser.add_argument('--target-lang', default='ru', help='Target language for translation (default: en)')
    
    args = parser.parse_args()
    process_video(args.input, args.output, args.target_lang)

if __name__ == "__main__":
    main()
