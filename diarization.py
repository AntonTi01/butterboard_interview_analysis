import os
import argparse
import torch
import tempfile
from config import HUGGINGFACE_TOKEN, MODEL_DIR
from utils.utils import download_diarization_models, get_device
from pyannote.audio import Pipeline
from wav_io.wav_io import transform_to_wavpcm, load_sound


# Проверка наличия необходимых моделей
def check_and_download_models():
    required_models = ["speaker-diarization-3.1", "segmentation-3.0"]
    
    for model in required_models:
        model_path = os.path.join(MODEL_DIR, model)
        if not os.path.exists(model_path):
            print(f"Модель {model} не найдена. Загружаем...")
            download_diarization_models()
            break
    print("Все модели на месте.")


def perform_diarization(input_audio, output_txt):
    print(f"Обрабатываем файл: {input_audio}")

    if not os.path.isfile(input_audio):
        raise FileNotFoundError(f"Файл '{input_audio}' не найден!")

    check_and_download_models()
    
    # Определяем устройство для вычислений
    device = get_device()

    # Если файл не WAV, конвертируем его в временный .wav
    tmp_wav_name = None
    if not input_audio.endswith(".wav"):
        print("Конвертация в WAV...")
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.wav') as fp:
            tmp_wav_name = fp.name
        transform_to_wavpcm(input_audio, tmp_wav_name)
        wav_audio_path = tmp_wav_name
    else:
        wav_audio_path = input_audio

    try:
        sound_data = load_sound(wav_audio_path)
        if sound_data is None:
            raise ValueError(f"Файл {wav_audio_path} пуст или повреждён.")
    except Exception as e:
        raise RuntimeError(f"Ошибка загрузки {wav_audio_path}: {str(e)}")

    config_path = os.path.join(MODEL_DIR, "speaker-diarization-3.1", "config.yaml")
    pipeline = Pipeline.from_pretrained(config_path).to(torch.device(device))

    diarization_result = pipeline({"uri": "interview", "audio": wav_audio_path})

    # Сохраняем результат в файл
    os.makedirs(os.path.dirname(output_txt), exist_ok=True)
    with open(output_txt, "w") as f:
        for turn, _, speaker in diarization_result.itertracks(yield_label=True):
            line = f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}"
            print(line)
            f.write(line + "\n")

    print(f"Диаризация завершена. Файл сохранён в {output_txt}")

    # Удаление временного .wav файла
    if tmp_wav_name and os.path.isfile(tmp_wav_name):
        os.remove(tmp_wav_name)
        print(f"Временный файл {tmp_wav_name} удалён.")

# Аргументы командной строки
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Выполнить диаризацию спикеров в аудиофайле.")
    parser.add_argument("--input", type=str, required=True, help="Путь к входному аудиофайлу")
    parser.add_argument("--output", type=str, required=True, help="Путь к сохранённому файлу с результатами (.txt)")
    
    args = parser.parse_args()
    
    perform_diarization(args.input, args.output)
