import os.path
from typing import Tuple, Union
import wave
import tempfile

import numpy as np
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError


TARGET_SAMPLING_FREQUENCY = 16_000


def load_sound(fname: str) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray], None]:
    """
    Loads .wav audio. Automatically converts to mono, 16kHz, 16-bit PCM if needed.

    Returns:
    - A waveform array for mono-channel sound
    - Tuple of two waveform arrays for two-channel sound
    """
    def _read_and_decode(filepath: str):
        with wave.open(filepath, 'rb') as fp:
            n_channels = fp.getnchannels()
            fs = fp.getframerate()
            bytes_per_sample = fp.getsampwidth()
            sound_length = fp.getnframes()
            sound_bytes = fp.readframes(sound_length)

        if sound_length == 0:
            return None

        if bytes_per_sample == 1:
            data = np.frombuffer(sound_bytes, dtype=np.uint8)
        else:
            data = np.frombuffer(sound_bytes, dtype=np.int16)

        if len(data.shape) != 1:
            raise ValueError(f'"{filepath}": the loaded data is wrong! Expected 1-d array, got {len(data.shape)}-d one.')

        if n_channels == 1:
            if bytes_per_sample == 1:
                return (data.astype(np.float32) - 128.0) / 128.0
            else:
                return data.astype(np.float32) / 32768.0
        else:
            ch1 = data[0::2]
            ch2 = data[1::2]
            if bytes_per_sample == 1:
                return (
                    (ch1.astype(np.float32) - 128.0) / 128.0,
                    (ch2.astype(np.float32) - 128.0) / 128.0,
                )
            else:
                return (
                    ch1.astype(np.float32) / 32768.0,
                    ch2.astype(np.float32) / 32768.0,
                )

    try:
        with wave.open(fname, 'rb') as fp:
            n_channels = fp.getnchannels()
            fs = fp.getframerate()
            bytes_per_sample = fp.getsampwidth()

        if n_channels in {1, 2} and fs == TARGET_SAMPLING_FREQUENCY and bytes_per_sample in {1, 2}:
            return _read_and_decode(fname)
        else:
            print(f'Автоконвертация "{fname}" (channels={n_channels}, fs={fs}, width={bytes_per_sample}) → mono, 16kHz, 16-bit')
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as tmp:
                transform_to_wavpcm(fname, tmp.name)
                return _read_and_decode(tmp.name)

    except wave.Error as e:
        raise ValueError(f'"{fname}": cannot be read as a valid WAV file. {str(e)}')

def transform_to_wavpcm(src_fname: str, dst_fname: str) -> None:
    found_idx = src_fname.rfind('.')
    if found_idx < 0:
        err_msg = f'The extension of the file "{src_fname}" is unknown. ' \
                  f'So, I cannot determine a format of this sound file.'
        raise ValueError(err_msg)
    if not os.path.isfile(src_fname):
        err_msg = f'The file "{src_fname}" does not exist!'
        raise IOError(err_msg)
    source_audio_extension = src_fname[(found_idx + 1):]
    try:
        audio = AudioSegment.from_file(src_fname, format=source_audio_extension)
    except CouldntDecodeError as e1:
        audio = None
        additional_err_msg = str(e1)
    except BaseException as e2:
        audio = None
        additional_err_msg = str(e2)
    else:
        additional_err_msg = ''
    if audio is None:
        err_msg = f'The file "{src_fname}" cannot be opened.'
        if additional_err_msg != '':
            err_msg += f' {additional_err_msg}'
        raise IOError(err_msg)
    if audio.channels != 1:
        audio.set_channels(1)
    if audio.frame_rate != TARGET_SAMPLING_FREQUENCY:
        audio.set_frame_rate(TARGET_SAMPLING_FREQUENCY)
    if audio.frame_width != 2:
        audio.set_sample_width(2)
    target_parameters = ['-ac', '1', '-ar', f'{TARGET_SAMPLING_FREQUENCY}', '-acodec', 'pcm_s16le']
    audio.export(dst_fname, format='wav', parameters=target_parameters)
