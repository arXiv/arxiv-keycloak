import zipfile
import wave
import lameenc
from io import BytesIO
import os
import re

BUFFER_SIZE = 2 * 1024 * 1024  # 2MB buffer
zip_path = "voices.zip"

filename_patten = re.compile(r'__([a-z0-9]).wav')

def alnum_to_mp3(alnums: str) -> BytesIO:
    buffer = bytearray(BUFFER_SIZE)
    zip_path = os.path.join(os.path.dirname(__file__), "voices.zip")
    voice_files = {}
    total_size = 0

    with zipfile.ZipFile(zip_path, "r") as z:

        for filename in z.namelist():
            matched = filename_patten.search(filename)
            if matched:
                voice_files[matched.group(1).lower()] = filename

        for letter in alnums:
            voice_file = voice_files[letter.lower()]

            with z.open(voice_file) as wav_file:
                with wave.open(BytesIO(wav_file.read()), "rb") as wf:
                    params = wf.getparams()
                    sample_rate = params.framerate
                    num_channels = params.nchannels
                    num_frames = params.nframes

                    frames = wf.readframes(num_frames)
                    frame_size = len(frames)
                    buffer[total_size : total_size + frame_size] = frames
                    total_size += frame_size

    # Initialize LAME encoder
    encoder = lameenc.Encoder()
    encoder.set_bit_rate(128)  # Set MP3 bitrate
    encoder.set_in_sample_rate(sample_rate)
    encoder.set_channels(num_channels)
    encoder.set_quality(2)

    # Encode to MP3
    mp3_data = encoder.encode(bytes(buffer[: total_size]))
    mp3_data += encoder.flush()
    mp3_buffer = BytesIO(mp3_data)
    return mp3_buffer
