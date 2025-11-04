# Переводчик субтитров для видео

[English version](README.md)

Python-приложение, которое извлекает аудио из видео, расшифровывает его с помощью Whisper и переводит полученные субтитры через Google Gemini.

## Docker (рекомендуется)

Запуск проекта в Docker уже включает FFmpeg и все зависимости Python, поэтому можно сразу обрабатывать ролики без локальной настройки окружения.

### Подготовка конфигурации

1. Скопируйте `.env.example` в `.env`.
2. Обновите значения, прежде всего `GEMINI_API_KEY` (Можно взять бесплатно на aistudio.google.com).
3. Создайте каталоги для исходных файлов и результатов:
   ```bash
   mkdir -p input output
   ```
   ```powershell
   New-Item -ItemType Directory -Force -Path input, output
   ```

### Сборка образа

```bash
docker build -t auto-translator .
```

### Запуск контейнера

Выполняйте команды из корня проекта, чтобы каталоги `./input` и `./output` стали доступны в контейнере как `/workspace/input` и `/workspace/output`.

#### Linux/macOS (Bash)

```bash
docker run --rm \
  --env-file .env \
  -v "$(pwd)":/workspace \
  auto-translator \
  python process_video.py --input /workspace/input/video.mp4 --output /workspace/output/video.mp3 --target-lang ru
```

#### Windows PowerShell

```powershell
docker run --rm `
  --env-file .env `
  -v "${PWD}:/workspace" `
  auto-translator `
  python process_video.py --input /workspace/input/video.mp4 --output /workspace/output/video.mp3 --target-lang ru
```

По умолчанию контейнер выполняет `python process_video.py --help`; при необходимости укажите свою команду, как показано выше.

### Docker Compose

Файл `docker-compose.yml` собирает тот же образ и примонтирует ваш проект в `/workspace`.

1. Скопируйте `.env.example` в `.env` и обновите значения под своё окружение.
2. Соберите сервис:
   ```bash
   docker compose build
   ```
3. Запускайте команды при необходимости:
   ```bash
   docker compose run --rm translator \
     python process_video.py \
     --input /workspace/input/video.mp4 \
     --output /workspace/output/video.mp3 \
     --target-lang ru
   ```

Передайте свою команду в `docker compose run translator`, чтобы выполнить другие сценарии, или опустите её, чтобы увидеть помощь по умолчанию.

## Возможности

- Извлечение аудио из видеофайлов
- Генерация субтитров с помощью модели Whisper
- Перевод субтитров на выбранный язык через Gemini
- Ограничение частоты запросов и параллельная обработка
- Поддержка формата субтитров SRT

## Требования

- Python 3.8 или новее
- FFmpeg в `PATH`
- Ключ API Google Gemini (aistudio.google.com)
- Зависимости из `requirements.txt`

## Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Vovch/auto-translator.git
   cd auto-translator
   ```

2. Создайте и активируйте виртуальное окружение:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/macOS
   python -m venv venv
   source venv/bin/activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Создайте файл `.env` в корне проекта (можно переименовать `.env.example`) и заполните параметры:
   ```env
   WHISPER_MODEL=small
   OUTPUT_FORMAT=srt
   AUDIO_CODEC=libmp3lame
   GEMINI_API_KEY=<ваш_google_api_key>
   GEMINI_MODEL=gemini-2.0-flash-exp

   # Параметры обработки перевода
   CHUNK_SIZE=6500
   PARALLEL_REQUESTS=15
   MAX_REQUESTS_PER_MINUTE=15
   CHUNK_SEPARATOR="\n\n"

   # Пример подсказки для перевода с сохранением структуры SRT
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
   Как зовут этого парня?
   Какая у него должность?

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

## Использование

### Полная обработка видео

Скрипт `process_video.py` последовательно извлекает аудио, расшифровывает его и переводит субтитры:

```bash
python process_video.py --input путь/к/видео.mp4 --target-lang ru --output путь/к/output.mp3
```

### Аргументы командной строки

- `--input` — путь к входному видео или SRT
- `--output` — путь к файлу с результирующим аудио
- `--target-lang` — целевой язык перевода (например, `es`, `ja`, `ru`)

## Переменные окружения

- `WHISPER_MODEL` — размер модели Whisper (`tiny`, `base`, `small`, `medium`, `large`)
- `OUTPUT_FORMAT` — формат файлов с транскриптом (`srt` по умолчанию)
- `AUDIO_CODEC` — кодек для аудио при извлечении (`libmp3lame`)
- `GEMINI_API_KEY` — ключ Google Gemini
- `GEMINI_MODEL` — модель Gemini для перевода
- `CHUNK_SIZE` — максимальный размер блока текста для перевода
- `PARALLEL_REQUESTS` — количество параллельных запросов перевода
- `MAX_REQUESTS_PER_MINUTE` — лимит запросов в минуту
- `CHUNK_SEPARATOR` — разделитель между блоками при сохранении результата
- `TRANSLATION_PROMPT` — настраиваемая подсказка для Gemini

## Лицензия

Проект распространяется по лицензии MIT. Подробности смотрите в файле [LICENSE](LICENSE).
