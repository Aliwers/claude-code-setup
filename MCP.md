# MCP-серверы

`install.sh` ставит четыре, которым не нужны ключи: **context7** (актуальные доки
библиотек), **playwright** (браузер), **ddg-search** (веб-поиск), **n8n-mcp**.

Остальные — вручную, каждый со своим ключом.

## Нужен свой API-ключ

```bash
# 21st.dev — генерация UI-компонентов. Ключ: https://21st.dev
claude mcp add -s user -t http 21st https://21st.dev/api/mcp -H "x-api-key: ТВОЙ_КЛЮЧ"

# ElevenLabs — синтез речи. Ключ: https://elevenlabs.io  (нужен pip install elevenlabs-mcp)
claude mcp add -s user \
  -e ELEVENLABS_API_KEY='ТВОЙ_КЛЮЧ' \
  -e ELEVENLABS_MCP_BASE_PATH="$HOME/Documents/elevenlabs-out" \
  elevenlabs -- python3 -m elevenlabs_mcp.server

# higgsfield — генерация видео/картинок, авторизация по OAuth при первом вызове
claude mcp add -s user -t http higgsfield https://mcp.higgsfield.ai/mcp
```

## Авторизация через OAuth

Не ключом, а входом в аккаунт: в сессии набрать `/mcp` и пройти по ссылке.
Это Figma, Supabase, Miro, Stripe, Vercel — они приезжают вместе с плагинами.

## GitHub-плагин

Плагину `github` нужен personal access token (scope `repo`, `read:org`):
<https://github.com/settings/tokens>. Положить в `~/.claude/settings.json`:

```json
{ "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..." } }
```

## Коннекторы claude.ai

Gmail, Google Calendar, Google Drive, Miro, Strava, Idiolect подключаются **не
локально**, а в настройках аккаунта на claude.ai → Connectors. Появляются во всех
сессиях автоматически.
