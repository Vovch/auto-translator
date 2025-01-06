import os
import re
import argparse
from dotenv import load_dotenv
import google.generativeai as genai
import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Semaphore
import time

# Load environment variables
load_dotenv()

class RateLimiter:
    def __init__(self, max_requests_per_minute):
        self.max_requests = max_requests_per_minute
        self.window_size = 60  # 60 seconds = 1 minute
        self.requests = []
        self.lock = Lock()
        self.semaphore = Semaphore(max_requests_per_minute)
    
    def wait_if_needed(self):
        with self.lock:
            current_time = time.time()
            # Remove old requests
            self.requests = [req_time for req_time in self.requests 
                           if current_time - req_time < self.window_size]
            
            if len(self.requests) >= self.max_requests:
                # Wait until the oldest request expires
                sleep_time = self.window_size - (current_time - self.requests[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.requests = self.requests[1:]
            
            self.requests.append(current_time)

def setup_gemini():
    """Setup Gemini API with configuration from environment variables"""
    api_key = os.getenv('GEMINI_API_KEY')
    model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')  # Default to gemini-1.5-flash if not specified

    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    return model

def split_srt_into_chunks(content, chunk_size=None):
    """Split SRT content into chunks while preserving subtitle blocks"""
    # Get chunk size from environment variable or use default
    if chunk_size is None:
        chunk_size = int(os.getenv('CHUNK_SIZE', '6500'))
    
    # Split into individual subtitle blocks
    blocks = re.split(r'\n\n+', content.strip())
    chunks = []
    current_chunk = []
    current_size = 0
    
    for block in blocks:
        block_size = len(block)
        if current_size + block_size + 2 > chunk_size and current_chunk:  # +2 for \n\n
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = []
            current_size = 0
        
        current_chunk.append(block)
        current_size += block_size + 2  # +2 for \n\n
    
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks

def translate_chunk(model, chunk, source_lang, target_lang, rate_limiter):
    """Translate a chunk of subtitles"""
    prompt = os.getenv('TRANSLATION_PROMPT', '''
You are an expert translator. Your task is to translate the given subtitle text from {source_lang} to {target_lang}.
The input will be in SRT format. Only translate the text content, keeping all numbers, timestamps, and formatting intact.
''')
    
    prompt = prompt.format(source_lang=source_lang, target_lang=target_lang)
    
    try:
        if rate_limiter:
            rate_limiter.wait_if_needed()
        
        response = model.generate_content(f"{prompt}\n\n{chunk}")
        translated_text = response.text.strip()
        
        # Clean up any potential formatting issues
        translated_text = re.sub(r'\\n', '\n', translated_text)  # Replace literal \n with newlines
        translated_text = re.sub(r'\n{3,}', '\n\n', translated_text)  # Normalize multiple newlines
        
        return translated_text
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return chunk

def translate_srt(input_file, output_file, source_lang="auto", target_lang="en", 
                 max_requests_per_minute=None, parallel_requests=None):
    """
    Translate SRT subtitle file
    
    Args:
        input_file (str): Path to input SRT file
        output_file (str): Path to output translated SRT file
        source_lang (str): Source language code (default: auto-detect)
        target_lang (str): Target language code
        max_requests_per_minute (int): Maximum API requests per minute (default: from env)
        parallel_requests (int): Number of parallel translation requests (default: from env)
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Get configuration from environment variables if not provided
    if max_requests_per_minute is None:
        max_requests_per_minute = int(os.getenv('MAX_REQUESTS_PER_MINUTE', '15'))
    if parallel_requests is None:
        parallel_requests = int(os.getenv('PARALLEL_REQUESTS', '5'))
    
    # Setup Gemini model and rate limiter
    model = setup_gemini()
    rate_limiter = RateLimiter(max_requests_per_minute)
    
    # Read and split content into chunks
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    chunks = split_srt_into_chunks(content)
    print(f"Split content into {len(chunks)} chunks")
    print(f"Using {parallel_requests} parallel requests with {max_requests_per_minute} max requests per minute")
    
    # Translate chunks in parallel
    with ThreadPoolExecutor(max_workers=parallel_requests) as executor:
        translated_chunks = list(executor.map(
            lambda chunk: translate_chunk(model, chunk, source_lang, target_lang, rate_limiter),
            chunks
        ))
    
    # Combine translated chunks using the same separator
    separator = '\n\n'
    translated_content = separator.join(translated_chunks)
    
    # Write translated content
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(translated_content)
    
    print(f"Translation completed. Output saved to: {output_file}")
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Translate SRT subtitle file')
    parser.add_argument('input', help='Input SRT file path')
    parser.add_argument('output', help='Output SRT file path')
    parser.add_argument('--source', default='auto', help='Source language code (default: auto)')
    parser.add_argument('--target', default='en', help='Target language code')
    parser.add_argument('--max-rpm', type=int, default=None, help='Maximum requests per minute (default: from env)')
    parser.add_argument('--parallel', type=int, default=None, help='Number of parallel requests (default: from env)')
    
    args = parser.parse_args()
    translate_srt(args.input, args.output, args.source, args.target, 
                 args.max_rpm, args.parallel)

if __name__ == "__main__":
    main()
