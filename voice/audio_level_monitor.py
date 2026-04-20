from __future__ import annotations

import math
import threading
import time
from array import array
from collections.abc import Callable
from contextlib import suppress

try:
    import pyaudio
except Exception:  # pragma: no cover - runtime optional dependency
    pyaudio = None


class AudioLevelMonitor:
    def __init__(
        self,
        callback: Callable[[float], None],
        *,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
    ) -> None:
        self._callback = callback
        self._sample_rate = sample_rate
        self._chunk_size = chunk_size
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._running or pyaudio is None:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, name="audio-level-monitor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _run(self) -> None:
        audio = pyaudio.PyAudio()
        stream = None
        level = 0.0
        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self._sample_rate,
                input=True,
                frames_per_buffer=self._chunk_size,
            )
            while self._running:
                try:
                    data = stream.read(self._chunk_size, exception_on_overflow=False)
                except Exception:
                    self._callback(0.0)
                    time.sleep(0.12)
                    continue

                level = self._calculate_level(data, previous=level)
                self._callback(level)
        except Exception:
            self._callback(0.0)
        finally:
            with suppress(Exception):
                if stream is not None:
                    stream.stop_stream()
            with suppress(Exception):
                if stream is not None:
                    stream.close()
            with suppress(Exception):
                audio.terminate()

    @staticmethod
    def _calculate_level(data: bytes, *, previous: float) -> float:
        if not data:
            return previous * 0.75

        samples = array("h")
        samples.frombytes(data)
        if not samples:
            return previous * 0.75

        square_sum = sum(sample * sample for sample in samples)
        rms = math.sqrt(square_sum / len(samples)) / 32768.0
        normalized = min(1.0, rms * 10.0)
        if normalized < 0.015:
            normalized = 0.0
        return previous * 0.65 + normalized * 0.35
