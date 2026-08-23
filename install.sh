#!/usr/bin/env bash
# Разворачивает набор скиллов/агентов/команд/правил/хуков в ~/.claude
# и ставит плагины + MCP-серверы. Идемпотентен, старое кладёт в бэкап.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DST="$HOME/.claude"
DIRS="skills agents commands rules hooks sounds"

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
warn() { printf '\033[33m  ! %s\033[0m\n' "$*"; }

command -v claude >/dev/null || { echo "Не найден claude CLI. Сначала поставь Claude Code."; exit 1; }
command -v python3 >/dev/null || warn "нет python3 — хуки озвучки и метки окна работать не будут"
command -v jq >/dev/null || warn "нет jq — statusLine будет пустой (brew install jq)"

mkdir -p "$DST/backups"

# ── 1. Бэкап того, что уже лежит ────────────────────────────────────────────
EXISTING=""
for d in $DIRS settings.json; do [ -e "$DST/$d" ] && EXISTING="$EXISTING $d"; done
if [ -n "$EXISTING" ]; then
  TS=$(date +%Y%m%d-%H%M%S)
  say "Бэкап текущего ~/.claude → backups/pre-setup-$TS.tgz"
  tar czf "$DST/backups/pre-setup-$TS.tgz" -C "$DST" $EXISTING
fi

# ── 2. Файлы ────────────────────────────────────────────────────────────────
say "Копирую $DIRS"
for d in $DIRS; do
  mkdir -p "$DST/$d"
  cp -R "$SRC/$d/." "$DST/$d/"
  echo "  $d"
done
chmod +x "$DST"/hooks/*.py 2>/dev/null || true
cp "$SRC/ECC-INSTALLED.md" "$DST/ECC-INSTALLED.md"

# ── 3. settings.json ────────────────────────────────────────────────────────
if [ -f "$DST/settings.json" ]; then
  cp "$SRC/settings.json" "$DST/settings.suggested.json"
  warn "settings.json уже был — эталон рядом: ~/.claude/settings.suggested.json, слей руками"
else
  cp "$SRC/settings.json" "$DST/settings.json"
  say "settings.json установлен"
fi

# ── 4. Маркетплейсы и плагины ───────────────────────────────────────────────
say "Маркетплейсы"
for m in anthropics/claude-plugins-official DietrichGebert/ponytail nextlevelbuilder/ui-ux-pro-max-skill; do
  claude plugin marketplace add "$m" --scope user 2>/dev/null || echo "  уже есть: $m"
done

say "Плагины"
OFFICIAL="context7 frontend-design superpowers code-review skill-creator playwright github
figma supabase telegram playground stripe hookify firecrawl miro mcp-tunnels
code-simplifier claude-md-management security-guidance vercel feature-dev mcp-server-dev"
for p in $OFFICIAL; do
  claude plugin install "$p@claude-plugins-official" -s user -y >/dev/null 2>&1 && echo "  + $p" || echo "  ? $p (пропущен)"
done
claude plugin install ponytail@ponytail -s user -y >/dev/null 2>&1 && echo "  + ponytail" || echo "  ? ponytail"
claude plugin install ui-ux-pro-max@ui-ux-pro-max-skill -s user -y >/dev/null 2>&1 && echo "  + ui-ux-pro-max" || echo "  ? ui-ux-pro-max"

# ── 5. MCP-серверы, которым не нужны ключи ──────────────────────────────────
say "MCP без ключей"
claude mcp add -s user -t http context7 https://mcp.context7.com/mcp 2>/dev/null && echo "  + context7" || echo "  = context7"
claude mcp add -s user playwright -- npx -y @playwright/mcp@latest 2>/dev/null && echo "  + playwright" || echo "  = playwright"
claude mcp add -s user ddg-search -- npx -y @oevortex/ddg_search 2>/dev/null && echo "  + ddg-search" || echo "  = ddg-search"
claude mcp add -s user -e MCP_MODE=stdio -e LOG_LEVEL=error -e DISABLE_CONSOLE_OUTPUT=true \
  n8n-mcp -- npx -y n8n-mcp@latest 2>/dev/null && echo "  + n8n-mcp" || echo "  = n8n-mcp"

say "Готово."
cat <<'TXT'
Осталось руками (нужны свои ключи/аккаунты) — см. MCP.md:
  • 21st.dev, ElevenLabs, higgsfield  — свои API-ключи
  • GitHub-плагин                     — свой personal access token
  • Figma / Supabase / Miro / Stripe / Vercel — авторизация через /mcp в сессии
Проверка: запусти `claude`, набери /plugin и /mcp
TXT
