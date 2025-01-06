import whisper
import argparse
import os
from tqdm import tqdm
import time
import torch

def transcribe_audio(audio_path, model_name="small", output_format="txt"):
    """
    Transcribe audio file using Whisper with automatic device selection
    
    Args:
        audio_path (str): Path to audio file
        model_name (str): Whisper model name (tiny, base, small, medium, large)
        output_format (str): Output format (txt or srt)
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Check if CUDA (NVIDIA GPU) is available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading Whisper model '{model_name}' using {device.upper()} device...")
    
    model = whisper.load_model(model_name)
    if device == "cuda":
        model = model.to(device)
    
    print("Transcribing audio... This may take a while.")
    result = model.transcribe(
        audio_path,
        verbose=True,
        fp16=(device == "cuda")  # Use FP16 only when using GPU
    )
    
    # Create output filename
    base_name = os.path.splitext(audio_path)[0]
    output_file = f"{base_name}_transcript.{output_format}"
    
    # Save the transcription
    if output_format == "txt":
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result["text"])
    elif output_format == "srt":
        # Generate SRT format with timestamps
        with open(output_file, "w", encoding="utf-8") as f:
            for i, segment in enumerate(result["segments"], 1):
                # Convert timestamps to SRT format
                start = time.strftime('%H:%M:%S,000', time.gmtime(segment["start"]))
                end = time.strftime('%H:%M:%S,000', time.gmtime(segment["end"]))
                text = segment["text"].strip()
                
                # Write SRT entry
                f.write(f"{i}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")
    
    print(f"\nTranscription saved to: {output_file}")
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Transcribe audio using Whisper')
    parser.add_argument('input', help='Input audio file path')
    parser.add_argument(
        '--model', 
        choices=['tiny', 'base', 'small', 'medium', 'large', 'turbo'],
        default='small',
        help='Whisper model to use (default: small)'
    )
    parser.add_argument(
        '--format',
        choices=['txt', 'srt'],
        default='srt',
        help='Output format (txt or srt with timestamps) (default: txt)'
    )
    
    args = parser.parse_args()
    transcribe_audio(args.input, args.model, args.format)

if __name__ == "__main__":
    main()
