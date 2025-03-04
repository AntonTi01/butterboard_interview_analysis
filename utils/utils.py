import math
from huggingface_hub import snapshot_download
from config import HUGGINGFACE_TOKEN, MODEL_DIR
import torch


def time_to_str(time_val: float) -> str:
    if not isinstance(time_val, float):
        raise ValueError(f'The time value {time_val} is not floating-point!')
    if time_val < 0.0:
        raise ValueError(f'The time value {time_val} is negative!')
    hours = int(math.floor(time_val / 3600.0))
    if hours == 0:
        s = '00'
    elif hours < 10:
        s = '0' + str(hours)
    else:
        s = str(hours)
    s += ':'
    time_val -= hours * 3600.0
    minutes = int(math.floor(time_val / 60.0))
    if minutes < 10:
        s += '0' + str(minutes)
    else:
        s += str(minutes)
    time_val -= minutes * 60.0
    s += ':'
    s += ('{0:06.3f}'.format(time_val)).replace('.', ',')
    return s

def download_diarization_models():
    snapshot_download(
        repo_id="pyannote/speaker-diarization-3.1",
        local_dir=f"{MODEL_DIR}/speaker-diarization-3.1",
        use_auth_token=HUGGINGFACE_TOKEN
    )
    snapshot_download(
        repo_id="pyannote/segmentation-3.0",
        local_dir=f"{MODEL_DIR}/segmentation-3.0",
        use_auth_token=HUGGINGFACE_TOKEN
    )

# Определение устройства (CUDA, MPS, CPU)
def get_device() -> str:
    if torch.cuda.is_available():
        return "cuda:0"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"