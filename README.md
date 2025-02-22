# Video Subtitle Translator

A Python-based tool that processes video files by extracting audio, generating subtitles using Whisper, and translating them to your desired language using Google's Gemini AI.

## Features

- Extract audio from video files
- Generate subtitles using OpenAI's Whisper model
- Translate subtitles to any supported language using Google's Gemini AI
- Rate limiting and parallel processing for efficient translation
- Support for SRT subtitle format

## Prerequisites

- Python 3.8 or higher
- FFmpeg installed and available in system PATH
- Google Gemini API key (aistudio.google.com)
- Required Python packages (see Installation section)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Vovch/auto-translator.git
cd auto-translator
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

3. Install the required Python packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your configuration:
```env
WHISPER_MODEL=small
OUTPUT_FORMAT=txt
AUDIO_CODEC=libmp3lame
GEMINI_API_KEY=your_google_api_key
GEMINI_MODEL=gemini-2.0-flash-exp

# Translation processing parameters
CHUNK_SIZE=6500
PARALLEL_REQUESTS=15
MAX_REQUESTS_PER_MINUTE=15
CHUNK_SEPARATOR="\n\n"

# Translation prompt with examples
TRANSLATION_PROMPT="You are an expert translator specializing in subtitle translation. Your task is to translate the given subtitle text from {source_lang} to {target_lang}. The input will be in SRT format.

IMPORTANT: Only translate the text content. DO NOT translate or modify:
1. Subtitle numbers
2. Timestamps
3. Empty lines between subtitles

Example input:
1
00:00:47,829 --> 00:00:48,871
What's the fella's line?
What's his line?

2
00:00:49,252 --> 00:00:50,461
Let him go, Orville.

Example output (to Russian):
1
00:00:47,829 --> 00:00:48,871
Чем этот парень занимается?
Какая у него профессия?

2
00:00:49,252 --> 00:00:50,461
Отпусти его, Орвилл.

Remember:
1. Keep subtitle numbers and timestamps exactly as they are
2. Only translate the text between timestamps and empty lines
3. Maintain the same number of lines per subtitle
4. Keep translations concise to match subtitle timing
5. Preserve all formatting and empty lines"

```

## Usage

### Individual Components

#### Extract Audio from Video
The `extract_audio.py` script allows you to extract audio from video files:

```bash
python extract_audio.py --input path/to/video.mp4 --output path/to/output.mp3
```

Parameters:
- `--input`: Path to input video file
- `--output`: (Optional) Path to output audio file. If not specified, will create one based on the input filename

#### Transcribe Audio to Subtitles
The `transcribe_audio.py` script transcribes audio files to SRT subtitles using Whisper:

```bash
python transcribe_audio.py --input path/to/audio.mp3 --model small --format srt
```

Parameters:
- `--input`: Path to input audio file
- `--model`: (Optional) Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
- `--format`: (Optional) Output format ('srt' or 'txt')

#### Process Complete Video
The `process_video.py` script combines all steps (extract audio, transcribe, and translate):

```bash
python process_video.py --input path/to/video.mp4 --target-lang ja
```

#### Translate Existing Subtitles
To translate an existing SRT file:

```bash
python translate_subtitles.py --input path/to/subtitles.srt --output translated_subtitles.srt --target-lang es
```

### Parameters

- `--input`: Path to input video file or SRT file
- `--output`: (Optional) Path to output file
- `--target-lang`: Target language code (e.g., 'es' for Spanish, 'ja' for Japanese)

## Environment Variables

- `WHISPER_MODEL`: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
- `OUTPUT_FORMAT`: Output format for subtitles (default: 'srt')
- `AUDIO_CODEC`: Audio codec for extraction (default: 'libmp3lame')
- `GEMINI_API_KEY`: Your Google Gemini API key
- `GEMINI_MODEL`: Gemini model to use for translation
- `CHUNK_SIZE`: Maximum size of text chunks for translation
- `PARALLEL_REQUESTS`: Number of parallel translation requests
- `MAX_REQUESTS_PER_MINUTE`: Rate limiting for API requests

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
