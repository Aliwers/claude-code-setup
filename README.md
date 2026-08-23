# Прокачка Claude Code — перенос набора

Слепок рабочей конфигурации: 105 скиллов, 38 агентов, 15 команд, 122 файла
правил, 24 плагина, 7 MCP-серверов, хуки и звуки. Секретов внутри нет — ключи
подставляются на месте (см. [MCP.md](MCP.md)).

## Установка

```bash
unzip claude-code-setup.zip && cd claude-code-setup
./install.sh
```

Скрипт кладёт бэкап текущего `~/.claude` в `~/.claude/backups/`, копирует
каталоги, ставит маркетплейсы и плагины, добавляет MCP без ключей. Идемпотентен —
можно гонять повторно. Требования: Claude Code, `python3`, `jq`, `node`.

После — открыть `claude`, проверить `/plugin` и `/mcp`.

---

## Что внутри

### `skills/` — 105 скиллов

Подгружаются по описанию, когда задача совпадает. Крупные группы (полный разбор —
[ECC-INSTALLED.md](ECC-INSTALLED.md)):

| Группа | Примеры |
|---|---|
| Инженерные основы (18) | `coding-standards` `api-design` `error-handling` `tdd-workflow` `e2e-testing` `deployment-patterns` `docker-patterns` `database-migrations` |
| Фронтенд и UI (12) | `accessibility` `design-system` `frontend-patterns` `motion-ui` `react-patterns` `react-performance` `browser-qa` |
| Бэкенд, данные, языки (10) | `backend-patterns` `python-patterns` `golang-patterns` `rust-patterns` `postgres-patterns` `redis-patterns` `prisma-patterns` |
| Агентная инженерия (21) | `agent-eval` `agent-harness-construction` `gan-style-harness` `council` `dev-team` `context-budget` `prompt-optimizer` |
| Гардрейлы и процесс (8) | `gateguard` `delivery-gate` `safety-guard` `santa-method` `intent-driven-development` |
| Исследование (6) | `deep-research` `search-first` `documentation-lookup` `seo` |
| Оркестрация `orch-*` (6) | `orch-build-mvp` `orch-add-feature` `orch-fix-defect` `orch-refine-code` |
| Стартап (12) | `product-lens` `market-research` `brand-discovery` `investor-materials` `content-engine` `crosspost` |
| Автоматизация сайтов (9) | `data-scraper-agent` `canary-watch` `ui-demo` `frontend-slides` `dashboard-builder` |
| Память между сессиями (2) | `ck` `continuous-learning-v2` |

Источник: [affaan-m/ecc](https://github.com/affaan-m/ecc) (MIT), выборка ~1/3 репо
— отраслевое и вендорское отброшено.

### `agents/` — 38 субагентов

Работают в своём контексте, возвращают результат. Ревьюеры по языкам
(`typescript-reviewer` `react-reviewer` `vue-reviewer` `python-reviewer`
`go-reviewer` `rust-reviewer`), качество (`code-reviewer` `security-reviewer`
`performance-optimizer` `silent-failure-hunter` `refactor-cleaner`),
планирование (`architect` `planner` `code-architect` `code-explorer`),
тесты и сборка (`tdd-guide` `e2e-runner` `build-error-resolver`), плюс
`a11y-architect` `seo-specialist` `marketing-agent` и GAN-тройка.

### `commands/` — 15 слэш-команд

Контекст не занимают, вызываются явно: `/plan` `/plan-prd` `/feature-dev`
`/gan-design` `/gan-build` `/santa-loop` `/ecc-code-review` `/test-coverage`
`/pr` `/checkpoint` `/save-session` `/resume-session` `/skill-create`
`/update-codemaps` `/aside`.

### `rules/` — библиотека правил, 23 набора

`common/` (база: стиль, git, тесты, безопасность, ревью) + стеки: `web`
`typescript` `react` `vue` `nuxt` `angular` `react-native` `python` `golang`
`rust` `java` `kotlin` `swift` `php` `ruby` `csharp` `cpp` `fsharp` `dart`
`perl` `arkts`.

`rules/README.md` и `rules/common/*` грузятся глобально во все сессии. Языковые
наборы — с `paths:`-фронтматтером, включаются только под свои файлы, так что
контекст не раздувают.

### `hooks/` + `sounds/` — обвязка (macOS)

- `speak-response.py` — Stop-хук, читает ответ вслух голосом Milena (ru).
  Заткнуть: `touch ~/.claude/.speak-off`. Голос менять в константе `VOICE`.
- `vscode-attention.py` — ставит `●` в заголовок окна VS Code, пока Claude ждёт
  ответа. Снимает, когда ответил. Считает сессии, чужой `window.title` не портит.
- `sounds/` — 48 вариантов звуковых сигналов, играет `done.wav` по завершении.
  Перебрать варианты: `afplay ~/.claude/sounds/done-5-tryam.wav`, понравившийся
  скопировать в `done.wav`.

Всё это в `settings.json`. Не нужно — выкинуть блок `hooks`.

### `settings.json`

Модель `opus`, `effortLevel: xhigh`, язык интерфейса `ru`, тёмная тема, голосовой
ввод в режиме hold, statusLine с моделью и веткой git, список плагинов и
маркетплейсов. Если у брата уже есть свой — install.sh положит эталон рядом как
`settings.suggested.json`, слить руками.

### Плагины — 24

Официальные (`anthropics/claude-plugins-official`): `superpowers` `context7`
`frontend-design` `code-review` `code-simplifier` `feature-dev` `skill-creator`
`playwright` `github` `figma` `supabase` `telegram` `playground` `stripe`
`hookify` `firecrawl` `miro` `mcp-tunnels` `claude-md-management`
`security-guidance` `vercel` `mcp-server-dev`.

Сторонние: [`ponytail`](https://github.com/DietrichGebert/ponytail) — режим
«ленивого сеньора», давит оверинжиниринг; включается `/ponytail full`.
[`ui-ux-pro-max`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) —
дизайн-скиллы (`/design` `/brand` `/slides` `/ui-styling`).

### MCP-серверы — 7

Без ключей ставит install.sh: `context7` `playwright` `ddg-search` `n8n-mcp`.
С ключами вручную: `21st` `elevenlabs` `higgsfield` — см. [MCP.md](MCP.md).

---

## Что не переносится

- **Ключи и токены** — вырезаны намеренно, брат заводит свои.
- **История, память, планы** (`projects/` `plans/` `sessions/`) — личное.
- **Коннекторы claude.ai** (Gmail, Calendar, Drive, Miro, Strava) — привязаны к
  аккаунту, подключаются на claude.ai → Connectors.
- **Подписка** — весь набор бесполезен без своего платного плана Claude.

## Известные дыры

| Что | Статус |
|---|---|
| `continuous-learning-v2` | CLI работает вручную, автонаблюдение за сессиями — нет (хуки завязаны на полную установку ECC) |
| `gateguard` `delivery-gate` `safety-guard` | В `settings.json` не прописаны — работают как инструкции при явном вызове, не как автогейты |
| `deep-research` | Хочет MCP firecrawl/exa. Плагин firecrawl стоит — после авторизации заработает |
| `data-scraper-agent` | Нужен бесплатный ключ Gemini API и GitHub Actions |
| `ck` | Скрипты на Node есть, session-start-хук не подключён |
| хуки и звуки | Только macOS (`say`, `afplay`) |
