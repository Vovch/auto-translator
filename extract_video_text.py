import os
import math
from dotenv import load_dotenv
from datetime import timedelta
import google.generativeai as genai
import cv2
import time
import argparse

load_dotenv()

API_KEY_ENV_VAR = "GEMINI_API_KEY"


def get_api_key():
    """Fetch the Gemini API key from environment variables."""
    api_key = os.getenv(API_KEY_ENV_VAR)
    if not api_key:
        raise ValueError(f"Please set {API_KEY_ENV_VAR} in your environment or .env file")
    return api_key


class VideoTextExtractor:
    def __init__(self, model_name="gemini-1.5-pro"):
        # Configure the API key
        self.api_key = get_api_key()
        genai.configure(api_key=self.api_key)
        
        # Print configuration for debugging
        print(f"Using model: {model_name}")
        print("Gemini API key loaded from environment variables.")
        
        try:
            self.model = genai.GenerativeModel(model_name=model_name)
        except Exception as e:
            print(f"Error initializing model: {str(e)}")
            raise
        
    def split_video(self, input_path, chunk_duration=1200):  # 1200 seconds = 20 minutes
        """Split video into chunks if longer than chunk_duration"""
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {input_path}")
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        total_duration = total_frames / fps
        
        if total_duration <= chunk_duration:
            cap.release()
            return [input_path]
        
        chunk_files = []
        num_chunks = math.ceil(total_duration / chunk_duration)
        base_name = os.path.splitext(input_path)[0]
        
        for i in range(num_chunks):
            start_time = i * chunk_duration
            end_time = min((i + 1) * chunk_duration, total_duration)
            
            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps)
            
            chunk_path = f"{base_name}_chunk_{i}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(chunk_path, fourcc, fps, 
                                (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                                 int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            for _ in range(start_frame, end_frame):
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
            
            out.release()
            chunk_files.append(chunk_path)
        
        cap.release()
        return chunk_files

    def process_chunk(self, video_path):
        """Process a single video chunk using Gemini API"""
        print(f"Processing {video_path}...")
        
        # Upload the video
        video_file = genai.upload_file(path=video_path)
        
        # Wait for processing
        while video_file.state.name == "PROCESSING":
            print('.', end='')
            time.sleep(10)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise ValueError(f"File processing failed: {video_path}")

        # Extract text with timestamps
        prompt = """Extract all text that appears in the video (labels, intertitles, subtitles) with their exact timestamps.
        Format the output as a list of entries with timestamps in HH:MM:SS format and the corresponding text.
        Only include entries where text actually appears."""

        response = self.model.generate_content(
            [video_file, prompt],
            request_options={"timeout": 600}
        )
        
        # Clean up the uploaded file
        video_file.delete()
        
        return response.text

    def parse_timestamps(self, text):
        """Parse the Gemini response into SRT format entries"""
        entries = []
        current_entry = None
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Look for timestamp patterns (HH:MM:SS or MM:SS)
            if ':' in line:
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    timestamp, content = parts
                    
                    # Convert timestamp to SRT format
                    if len(timestamp.split(':')) == 2:
                        timestamp = f"00:{timestamp}"
                    
                    # Calculate end time (assume 3 seconds duration)
                    start_time = sum(x * int(t) for x, t in zip([3600, 60, 1], timestamp.split(':')))
                    end_time = start_time + 3
                    
                    entries.append({
                        'index': len(entries) + 1,
                        'start': timestamp,
                        'end': str(timedelta(seconds=end_time)),
                        'text': content.strip()
                    })
        
        return entries

    def format_srt(self, entries):
        """Format entries in SRT format"""
        srt_content = ""
        for entry in entries:
            srt_content += f"{entry['index']}\n"
            srt_content += f"{entry['start']} --> {entry['end']}\n"
            srt_content += f"{entry['text']}\n\n"
        return srt_content

    def process_video(self, input_path, output_path, chunk_duration=1200):
        """Process entire video and create SRT file"""
        # Split video if necessary
        chunk_files = self.split_video(input_path, chunk_duration)
        
        all_entries = []
        time_offset = 0
        
        for chunk_file in chunk_files:
            # Process each chunk
            chunk_text = self.process_chunk(chunk_file)
            chunk_entries = self.parse_timestamps(chunk_text)
            
            # Adjust timestamps based on chunk position
            for entry in chunk_entries:
                entry['index'] = len(all_entries) + 1
                # Add time offset for chunks after the first
                if chunk_file != chunk_files[0]:
                    start_parts = entry['start'].split(':')
                    total_seconds = int(start_parts[0]) * 3600 + int(start_parts[1]) * 60 + int(start_parts[2])
                    total_seconds += time_offset
                    entry['start'] = str(timedelta(seconds=total_seconds))
                    
                    end_parts = entry['end'].split(':')
                    total_seconds = int(end_parts[0]) * 3600 + int(end_parts[1]) * 60 + int(end_parts[2])
                    total_seconds += time_offset
                    entry['end'] = str(timedelta(seconds=total_seconds))
                
            all_entries.extend(chunk_entries)
            
            # Update time offset for next chunk
            if chunk_file != chunk_files[0]:
                time_offset += chunk_duration
            
            # Clean up temporary chunk files
            if len(chunk_files) > 1 and os.path.exists(chunk_file):
                os.remove(chunk_file)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Write final SRT file
        srt_content = self.format_srt(all_entries)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)

def main():
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Extract text from video using Google Gemini API')
    parser.add_argument('input', help='Input video file path')
    parser.add_argument('--output', '-o', help='Output SRT file path (default: input_extracted.srt)')
    parser.add_argument('--chunk-duration', '-c', type=int, default=1200,
                       help='Duration of video chunks in seconds (default: 1200)')
    parser.add_argument('--model', '-m', default=os.getenv('GEMINI_MODEL', 'gemini-1.5-pro'),
                       help='Gemini model name (default: from GEMINI_MODEL env var or gemini-1.5-pro)')
    
    args = parser.parse_args()
    
    # Ensure API key is available before processing
    _ = get_api_key()
    
    # Set default output path if not provided
    if not args.output:
        base_name = os.path.splitext(args.input)[0]
        args.output = f"{base_name}_extracted.srt"
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    
    # Initialize extractor and process video
    extractor = VideoTextExtractor(model_name=args.model)
    try:
        extractor.process_video(args.input, args.output, chunk_duration=args.chunk_duration)
        print(f"Successfully processed video. Output saved to: {args.output}")
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        raise

if __name__ == "__main__":
    main()
