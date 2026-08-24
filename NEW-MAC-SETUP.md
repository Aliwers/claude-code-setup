# Второй мак с нуля → рабочий Claude Code

Репозиторий с набором: https://github.com/Aliwers/claude-code-setup

Порядок жёсткий: 1 → 2 → 3 → 4 → 5. Шаг 4 (`install.sh`) требует уже
установленного `claude`, иначе выйдет с ошибкой.

---

## 0. Что нужно иметь под рукой

- Apple ID для App Store (не обязателен, если ставить всё через .pkg/curl)
- Аккаунт Anthropic с активной подпиской (тот же, что на первом маке)
- Доступ к GitHub-аккаунту `Aliwers`

---

## 1. База системы

```bash
# 1.1 Command Line Tools — даёт git, компиляторы. Откроет окно установки.
xcode-select --install
# проверка (после установки):
git --version

# 1.2 Node.js LTS — нужен для MCP-серверов, они запускаются через npx.
# Скачать .pkg с https://nodejs.org  → установить → проверить:
node -v      # ждём v22+ или v24+
npx -v

# 1.3 jq — нужен для строки статуса. В macOS 15+ уже есть:
jq --version
# если "command not found" — https://jqlang.github.io/jq/download/

# 1.4 python3 — нужен для хуков озвучки и метки окна:
python3 -V
# если нет — .pkg с https://www.python.org/downloads/macos/
```

Homebrew ставить необязательно — на первом маке его нет, всё работает.

---

## 2. Claude Code

```bash
# 2.1 Установка (нативный установщик — так стоит на первом маке)
curl -fsSL https://claude.ai/install.sh | bash

# 2.2 Добавить в PATH, если оболочка его не видит
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 2.3 Проверка
claude --version     # нужна >= 2.1

# 2.4 Первый запуск и вход в аккаунт
claude
# откроется браузер → войти тем же аккаунтом Anthropic → вернуться в терминал
# в сессии проверить: /status
```

---

## 3. VS Code + расширение

```bash
# 3.1 Скачать VS Code: https://code.visualstudio.com/download (Apple Silicon)
#     Перетащить в /Applications, запустить.

# 3.2 Включить команду `code` в терминале:
#     в VS Code нажать Cmd+Shift+P → "Shell Command: Install 'code' command in PATH"
code --version

# 3.3 Расширение Claude Code
#     Способ А (сам поставится): открыть VS Code, Ctrl+` → в терминале набрать `claude`
#     Способ Б (вручную):
code --install-extension anthropic.claude-code
```

После этого `Cmd+Esc` открывает Claude прямо в VS Code.

---

## 4. Раскатка набора из GitHub

```bash
# 4.1 Доступ к репо. Если он приватный — сначала авторизоваться:
#     скачать gh с https://cli.github.com или сразу:
gh auth login          # если gh уже есть
#     Публичный репо — этот шаг пропустить.

# 4.2 Клонировать
mkdir -p ~/Documents && cd ~/Documents
git clone https://github.com/Aliwers/claude-code-setup.git
cd claude-code-setup

# 4.3 ПРОЧИТАТЬ, что скрипт делает — там подробно про перезапись и откат
open INSTALL.md      # или: cat INSTALL.md

# 4.4 Запустить
./install.sh
```

Скрипт разложит `skills/ agents/ commands/ rules/ hooks/ sounds/` в `~/.claude`,
поставит 3 маркетплейса, 24 плагина и 4 MCP-сервера без ключей
(context7, playwright, ddg-search, n8n-mcp). На чистом маке `settings.json`
встанет как есть — сливать вручную ничего не придётся.

Откат, если что: `tar xzf ~/.claude/backups/pre-setup-*.tgz -C ~/.claude`

---

## 5. То, чего в репо НЕТ — ключи и авторизации

В репозитории намеренно нет ни одного токена. После `install.sh` донастроить
руками (полные команды — в `MCP.md` репозитория):

| Что | Как |
|---|---|
| GitHub-плагин | выпустить **новый** PAT: https://github.com/settings/tokens (scope `repo`, `read:org`) → положить в `~/.claude/settings.json` в блок `env` как `GITHUB_PERSONAL_ACCESS_TOKEN` |
| Figma, Supabase, Miro, Stripe, Vercel | запустить `claude`, набрать `/mcp` → пройти OAuth по ссылке |
| higgsfield | `/mcp` → OAuth при первом вызове |
| 21st.dev, ElevenLabs | свои API-ключи, команды в `MCP.md` |
| Gmail, Calendar, Drive, Strava | не локально — на claude.ai → Settings → Connectors. Приедут сами, аккаунт тот же |

Блок `env` в `settings.json` выглядит так:

```json
{
  "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_ТВОЙ_НОВЫЙ_ТОКЕН" },
  "model": "opus"
}
```

---

## 6. Проверка, что всё встало

```bash
claude
```

В сессии:

| Команда | Что ждём |
|---|---|
| `/status` | аккаунт и подписка на месте |
| `/plugin` | 24 плагина |
| `/mcp` | 4 сервера сразу, остальные — после авторизации |
| `/skills` | около 105 скиллов |
| строка статуса внизу | модель + папка + ветка (пусто = нет `jq`) |

Затем скопировать в первую сессию промпт из §7 файла `INSTALL.md` — Клод сам
расскажет, что у него теперь есть.

---

## 7. Что заметно сразу и как выключить

| Поведение | Выключить |
|---|---|
| читает ответы вслух по-русски | `touch ~/.claude/.speak-off` |
| звук по завершении ответа | убрать строку `afplay` из `settings.json` |
| точка `●` в заголовке окна VS Code | убрать блок `vscode-attention.py` |
| модель `opus` + `effortLevel: xhigh` (дорого) | `"model": "sonnet"`, `"effortLevel": "medium"` |
| режим «ленивого сеньора» | `/ponytail lite` или `stop ponytail` |

---

## ⚠️ Безопасность — сделать до переноса

В `~/.claude/settings.json` **на первом маке** GitHub-токен лежит открытым
текстом. В репозиторий он не попал (проверено по всей истории коммитов — там
только плейсхолдер `ghp_...`), но:

1. Отозвать этот токен: https://github.com/settings/tokens → Delete
2. Выпустить два новых — отдельно для каждого мака
3. На новый мак **не копировать** `settings.json` с первого — только тот,
   что приезжает из репозитория, и вписать в него свой новый токен
