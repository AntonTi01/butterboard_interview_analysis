import os
import sys
import argparse
import logging
from speech_to_docx import perform_transcribation
from diarization import perform_diarization
from postprocessing import process_transcription_file

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(input_audio, model_path, enable_diarization, enable_postprocessing):
    logger.info(f"Старт пайплайна для {input_audio}")

    # Создаём структуру директорий
    raw_dir = "results/raw"
    postprocessed_dir = "results/postprocessed"
    diarization_dir = "results/diarization"
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(postprocessed_dir, exist_ok=True)
    os.makedirs(diarization_dir, exist_ok=True)

    # Получаем имя файла без расширения
    base_name = os.path.splitext(os.path.basename(input_audio))[0]

    # Определяем пути выходных файлов
    output_transcription = os.path.join(raw_dir, f"{base_name}.docx")
    postprocessed_output = os.path.join(postprocessed_dir, f"{base_name}_cleaned.docx")
    diarization_output = os.path.join(diarization_dir, f"{base_name}_diarization.txt")

    # 1. Выполняем транскрипцию
    logger.info("Этап 1: Транскрипция...")
    
    sys.argv = [
        "speech_to_docx.py",
        "--input", input_audio,
        "--output", output_transcription,
        "--model", model_path
    ]
    perform_transcribation()

    # 2. Опционально: Диаризация
    if enable_diarization:
        logger.info("Этап 2: Диаризация...")
        perform_diarization(input_audio, diarization_output)
        logger.info(f"Результат диаризации сохранён в {diarization_output}")

    # 3. Опционально: Постобработка
    if enable_postprocessing:
        logger.info("Этап 3: Постобработка...")
        process_transcription_file(output_transcription, postprocessed_output)
        logger.info(f"Файл после постобработки сохранён в {postprocessed_output}")

    logger.info("Пайплайн завершён!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Запуск пайплайна ASR + Diarization + Postprocessing")
    parser.add_argument("--input", type=str, required=True, help="Путь к входному аудиофайлу")
    parser.add_argument("--model", type=str, default="models/ru", help="Путь к папке с моделями")
    parser.add_argument("--enable_diarization", action="store_true", help="Включить диаризацию")
    parser.add_argument("--enable_postprocessing", action="store_true", help="Включить постобработку")

    args = parser.parse_args()
    main(args.input, args.model, args.enable_diarization, args.enable_postprocessing)
