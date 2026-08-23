#!/usr/bin/env python3
"""Stop-хук: читает вслух последний ответ Claude системным голосом macOS.

Никогда не блокирует сессию: say запускается в фоне, выход всегда 0.
Самопроверка: python3 speak-response.py --selftest
"""

import json
import os
import re
import subprocess
import sys

MAX_CHARS = 600
VOICE = "Milena"  # ru_RU; список голосов: say -v '?'
MUTE_FLAG = os.path.expanduser("~/.claude/.speak-off")  # есть файл — молчим


def clean(text: str) -> str:
    """Убирает из markdown всё, что звучит вслух как мусор."""
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)  # блоки кода
    text = re.sub(r"^\s*\|.*$", "", text, flags=re.MULTILINE)  # строки таблиц
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)  # ссылки -> текст
    text = re.sub(r"[`*_#>]", "", text)  # разметка
    text = re.sub(r"^\s*[-+]\s+", "", text, flags=re.MULTILINE)  # маркеры списка
    text = re.sub(r"[^\w\s.,!?:;()«»\"'—-]", " ", text, flags=re.UNICODE)  # эмодзи и пр.
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > MAX_CHARS:  # режем по границе предложения
        head = text[:MAX_CHARS]
        cut = max(head.rfind(". "), head.rfind("! "), head.rfind("? "))
        text = head[: cut + 1] if cut > MAX_CHARS // 2 else head
    return text


def last_assistant_text(transcript_path: str) -> str:
    """Последнее непустое текстовое сообщение ассистента из JSONL-транскрипта."""
    with open(transcript_path, encoding="utf-8") as f:
        lines = f.readlines()

    for line in reversed(lines):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("type") != "assistant":
            continue
        content = rec.get("message", {}).get("content", [])
        if isinstance(content, str):
            return content
        parts = [b.get("text", "") for b in content if b.get("type") == "text"]
        joined = " ".join(p for p in parts if p).strip()
        if joined:
            return joined
    return ""


def main() -> None:
    if os.path.exists(MUTE_FLAG):
        return

    data = json.load(sys.stdin)
    path = data.get("transcript_path")
    if not path or not os.path.exists(path):
        return

    text = clean(last_assistant_text(path))
    if len(text) < 3:
        return

    subprocess.run(["pkill", "-x", "say"], capture_output=True)  # обрываем прошлую фразу
    subprocess.Popen(
        ["say", "-v", VOICE, text],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,  # переживает завершение хука
    )


def selftest() -> None:
    assert clean("Вот код:\n```py\nprint(1)\n```\nГотово.") == "Вот код: Готово."
    assert clean("Смотри [файл](src/a.ts) тут") == "Смотри файл тут"
    assert clean("| a | b |\n| - | - |\nПосле таблицы") == "После таблицы"
    assert clean("**Важно** и `код`") == "Важно и код"
    assert clean("- пункт один\n- пункт два") == "пункт один пункт два"
    long = "Первое предложение. " + "слово " * 300
    assert len(clean(long)) <= MAX_CHARS
    assert clean("Готово ✅ 🎉") == "Готово"
    print("selftest OK")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    try:
        main()
    except Exception:
        pass  # озвучка не имеет права ломать сессию
    sys.exit(0)
