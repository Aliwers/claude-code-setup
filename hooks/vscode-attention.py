#!/usr/bin/env python3
"""Точка у названия окна VS Code, пока Claude Code ждёт ответа.

    vscode-attention.py on|off      (JSON хука приходит на stdin, берём .cwd)

Помечаем окно рабочей папки через window.title в .vscode/settings.json —
VS Code подхватывает файл на лету, поэтому точка появляется без перезапуска.
Чужой window.title сохраняем: точку приписываем спереди и снимаем её же.

В одной папке может работать несколько сессий, поэтому каждая ждущая держит
свою метку в ~/.claude/attention/<папка>/<сессия>: точка гаснет, только когда
не ждёт ни одна. Иначе соседняя вкладка снимала бы чужую пометку.
"""
import hashlib
import json
import os
import sys
import time

DOT = "● "
# Штатный шаблон заголовка VS Code — подставляем, если своего у пользователя нет.
DEFAULT_TITLE = "${dirty}${activeEditorShort}${separator}${rootName}${separator}${profileName}"
TITLE_KEY = "window.title"
COLOR_KEY = "workbench.colorCustomizations"
# Цвета прошлой версии хука: вычищаем их везде, где успели прописаться.
LEGACY_COLORS = (
    "titleBar.activeBackground", "titleBar.activeForeground",
    "titleBar.inactiveBackground", "titleBar.inactiveForeground",
    "titleBar.border", "statusBar.background", "statusBar.foreground",
    "statusBar.border", "window.activeBorder", "window.inactiveBorder",
)


STATE = os.path.expanduser("~/.claude/attention")
STALE = 12 * 3600   # метка брошенной сессии сама протухает за полсуток


def marks_dir(root):
    return os.path.join(STATE, hashlib.sha1(root.encode()).hexdigest()[:12])


def waiting_sessions(root, session, turn_on):
    """Ставит/снимает метку сессии и говорит, ждёт ли кто-нибудь ещё."""
    path = marks_dir(root)
    mark = os.path.join(path, session)
    try:
        os.makedirs(path, exist_ok=True)
        if turn_on:
            open(mark, "w").close()
        elif os.path.exists(mark):
            os.remove(mark)
        now = time.time()
        alive = 0
        for name in os.listdir(path):
            stale = os.path.join(path, name)
            if now - os.path.getmtime(stale) > STALE:
                os.remove(stale)
            else:
                alive += 1
        return alive > 0
    except OSError:
        return turn_on      # не смогли посчитать — ведём себя как раньше


def hook_payload():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def workspace_dir(payload):
    return payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def ignore_locally(root):
    """.vscode/ в локальный exclude — чтобы файл не всплывал в git status."""
    exclude = os.path.join(root, ".git", "info", "exclude")
    if not os.path.isdir(os.path.join(root, ".git")):
        return                      # не репозиторий или worktree — не лезем
    try:
        os.makedirs(os.path.dirname(exclude), exist_ok=True)
        if os.path.exists(exclude):
            with open(exclude) as f:
                if any(line.strip() == ".vscode/" for line in f):
                    return
        with open(exclude, "a") as f:
            f.write(".vscode/\n")
    except OSError:
        pass


def strip_legacy(settings):
    colors = settings.get(COLOR_KEY)
    if not isinstance(colors, dict):
        return
    for key in LEGACY_COLORS:
        colors.pop(key, None)
    if not colors:
        settings.pop(COLOR_KEY, None)


def main():
    turn_on = (sys.argv[1] if len(sys.argv) > 1 else "on") == "on"
    payload = hook_payload()
    root = workspace_dir(payload)
    session = str(payload.get("session_id") or "unknown").replace("/", "_")[:36]
    try:    # ВРЕМЕННО: кто и когда дёргает скрипт
        import time
        with open(os.path.expanduser("~/.claude/attention.log"), "a") as log:
            log.write("%s  %-3s  session=%s  %s\n" % (
                time.strftime("%H:%M:%S"), sys.argv[1] if len(sys.argv) > 1 else "?",
                str(payload.get("session_id"))[:8], root))
    except OSError:
        pass
    turn_on = waiting_sessions(root, session, turn_on)
    path = os.path.join(root, ".vscode", "settings.json")

    settings = {}
    if os.path.exists(path):
        try:
            with open(path) as f:
                settings = json.load(f)
        except Exception:
            return                  # файл с комментариями или битый — не трогаем чужое
        if not isinstance(settings, dict):
            return
    elif not turn_on:
        return                      # снимать нечего

    strip_legacy(settings)

    title = settings.get(TITLE_KEY)
    if not isinstance(title, str):
        title = None

    if turn_on:
        base = title if title is not None else DEFAULT_TITLE
        settings[TITLE_KEY] = base if base.startswith(DOT) else DOT + base
    elif title is not None and title.startswith(DOT):
        base = title[len(DOT):]
        if base == DEFAULT_TITLE:
            settings.pop(TITLE_KEY, None)   # свой заголовок пользователь не задавал
        else:
            settings[TITLE_KEY] = base

    if not settings:
        if os.path.exists(path):
            os.remove(path)         # файл был только под пометку — не оставляем мусор
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)           # атомарно: VS Code не увидит полупустой файл
    if turn_on:
        ignore_locally(root)


if __name__ == "__main__":
    main()
