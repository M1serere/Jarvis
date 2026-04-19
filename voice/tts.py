from __future__ import annotations

import asyncio
import re
import time
import uuid
from pathlib import Path

import edge_tts
import pygame
import pyttsx3

from core.config import (
    EDGE_TTS_PITCH,
    EDGE_TTS_RATE,
    EDGE_TTS_VOICE,
    PYTTSX3_RATE,
    TTS_PROVIDER,
    TTS_TEMP_DIR,
)


class TextToSpeech:
    def __init__(self) -> None:
        self.engine = pyttsx3.init()
        self._audio_player_available = False
        self._configure_fallback_voice()

    def _configure_fallback_voice(self) -> None:
        voices = self.engine.getProperty("voices")

        for voice in voices:
            voice_name = getattr(voice, "name", "").lower()
            if "male" in voice_name or "david" in voice_name:
                self.engine.setProperty("voice", voice.id)
                break

        self.engine.setProperty("rate", PYTTSX3_RATE)

    def _init_audio_player(self) -> None:
        if self._audio_player_available:
            return

        if pygame.mixer.get_init():
            self._audio_player_available = True
            return

        pygame.mixer.init()
        self._audio_player_available = True

    def speak(self, text: str) -> None:
        prepared_text = self._prepare_text(text)

        if not prepared_text:
            return

        print(f"🔊 Jarvis: {prepared_text}")

        if TTS_PROVIDER == "edge":
            try:
                self._speak_with_edge(prepared_text)
                return
            except Exception as e:
                print(f"⚠️ edge-tts failed, fallback to pyttsx3: {e}")

        self._speak_with_pyttsx3(prepared_text)

    def _prepare_text(self, text: str) -> str:
        cleaned = text.strip()

        # Чуть чище звучит, если убрать markdown-артефакты
        cleaned = cleaned.replace("**", "")
        cleaned = cleaned.replace("`", "")
        cleaned = cleaned.replace("#", "")
        cleaned = re.sub(r"\s+", " ", cleaned)

        # Небольшая нормализация для более "собранной" речи
        cleaned = cleaned.replace("...", "…")

        return cleaned.strip()

    def _split_text(self, text: str, max_len: int = 220) -> list[str]:
        parts = re.split(r"(?<=[.!?…])\s+", text)
        chunks: list[str] = []
        current = ""

        for part in parts:
            if not part:
                continue

            if len(current) + len(part) + 1 <= max_len:
                current = f"{current} {part}".strip()
            else:
                if current:
                    chunks.append(current)
                current = part.strip()

        if current:
            chunks.append(current)

        return chunks or [text]

    def _speak_with_edge(self, text: str) -> None:
        for chunk in self._split_text(text):
            file_path = TTS_TEMP_DIR / f"tts_{uuid.uuid4().hex}.mp3"

            try:
                asyncio.run(self._save_edge_audio(chunk, file_path))
                self._play_audio_file(file_path)
            finally:
                self._safe_delete(file_path)

    async def _save_edge_audio(self, text: str, file_path: Path) -> None:
        communicate = edge_tts.Communicate(
            text=text,
            voice=EDGE_TTS_VOICE,
            rate=EDGE_TTS_RATE,
            pitch=EDGE_TTS_PITCH,
        )
        await communicate.save(str(file_path))

    def _play_audio_file(self, file_path: Path) -> None:
        self._init_audio_player()
        pygame.mixer.music.load(str(file_path))
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        try:
            pygame.mixer.music.unload()
        except Exception:
            pass

    def _safe_delete(self, file_path: Path) -> None:
        for _ in range(10):
            try:
                if file_path.exists():
                    file_path.unlink()
                return
            except PermissionError:
                time.sleep(0.1)
            except Exception:
                return

    def _speak_with_pyttsx3(self, text: str) -> None:
        self.engine.say(text)
        self.engine.runAndWait()
