"""
This file contains the audio utilities.
"""

from io import BytesIO

from pydub import AudioSegment


class Audio:
    """
    Audio utilities.
    """

    def file_to_wav(file: bytes) -> BytesIO:
        """
        Converts bytes of audio file to wav bytes.

        :param file: The file to convert.
        :type file: bytes

        :return: The wav bytes.
        :rtype: BytesIO
        """
        wav_bytes = BytesIO()
        audio = AudioSegment.from_file(BytesIO(file))
        audio.export(wav_bytes, format="wav")
        wav_bytes.seek(0)
        return wav_bytes
