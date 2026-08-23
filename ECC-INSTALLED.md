# ECC — установленный набор

Источник: <https://github.com/affaan-m/ecc> (MIT, лицензия в `skills/LICENSE-ECC.txt`).
Установлено вручную, выборочно — **не** через `/plugin install ecc@ecc`.
Дата установки: 2026-08-15.

Взято из репозитория:

| Категория | Установлено | Всего в репо | Куда |
|---|---|---|---|
| Скиллы | 104 | 284 | `~/.claude/skills/` |
| Агенты | 38 | 68 | `~/.claude/agents/` |
| Команды | 15 | 94 | `~/.claude/commands/` |
| Правила | 22 набора / 122 файла | всё | `~/.claude/rules/` (библиотека) |

Отбор — универсальное плюс профиль пользователя: веб/фронтенд, стартапы,
автоматизация сайтов. Отраслевая и вендорская специфика пропущена, см. в конце.

---

## Команды (`~/.claude/commands/`, 15)

Вызываются явно, **контекст сессии не занимают**.

| Команда | Что делает |
|---|---|
| `/gan-design` | Цикл генератор↔оценщик для фронтенд-дизайна. По умолчанию до 10 итераций, порог 7.5/10 |
| `/gan-build` | То же для реализации фич |
| `/santa-loop` | Два независимых ревьюера, оба должны пропустить |
| `/plan-prd` | Проблема-ориентированный PRD → `.claude/prds/{name}.prd.md`, останавливается до «как» |
| `/plan` | План реализации: требования, риски, пошаговая декомпозиция |
| `/feature-dev` | Разработка фичи с упором на понимание кодовой базы |
| `/save-session`, `/resume-session` | Состояние работы в `~/.claude/session-data/` и обратно |
| `/skill-create` | Анализ git-истории репо → генерация SKILL.md с твоими паттернами |
| `/ecc-code-review` | Ревью локального диффа или GitHub PR. **Переименована** из `code-review`, чтобы не конфликтовать со встроенным `/code-review` |
| `/test-coverage` | Анализ покрытия, дописывание недостающих тестов |
| `/pr` | Создание GitHub PR из текущей ветки |
| `/checkpoint` | Чекпоинты рабочего процесса после верификации |
| `/update-codemaps` | Token-lean карта архитектуры проекта |
| `/aside` | Побочный вопрос без потери контекста текущей задачи |

## Правила (`~/.claude/rules/`)

Хранятся как **библиотека**, а не как активные правила: у файлов есть
`paths:`-фронтматтер (`**/*.css`, `**/*.html`, `**/*.tsx` и т.д.), и ECC
устанавливает их в конкретный проект через свой `install.sh`. Чтобы задействовать
в проекте — скопировать `rules/common/` + нужный стек в `<проект>/.claude/rules/`
и сослаться из `CLAUDE.md` проекта.

Наборы: `common` (всегда база) + `web` `typescript` `react` `vue` `nuxt` `angular`
`react-native` `python` `golang` `rust` `java` `kotlin` `swift` `php` `ruby` `csharp`
`cpp` `fsharp` `dart` `perl` `arkts`.

Для статических сайтов актуальны `common/` + `web/` (coding-style, design-quality,
performance, security, testing, patterns, hooks).

---

## Агенты (`~/.claude/agents/`, 38)

**Архитектура и планирование** — `architect` `planner` `code-architect`
`code-explorer` `spec-miner`

**Ревью и качество** — `code-reviewer` `code-simplifier` `refactor-cleaner`
`security-reviewer` `performance-optimizer` `silent-failure-hunter`
`type-design-analyzer` `comment-analyzer` `pr-test-analyzer` `database-reviewer`

**Тесты и сборка** — `tdd-guide` `e2e-runner` `build-error-resolver`
`react-build-resolver`

**Ревьюеры по языкам** — `typescript-reviewer` `react-reviewer` `vue-reviewer`
`python-reviewer` `go-reviewer` `rust-reviewer`

**Документация, доступность, SEO, маркетинг** — `doc-updater` `docs-lookup`
`a11y-architect` `seo-specialist` `marketing-agent`

**GAN-харнесс** — `gan-planner` `gan-generator` `gan-evaluator`

**Открытый код** — `opensource-forker` `opensource-sanitizer` `opensource-packager`

**Мета** — `agent-evaluator` `harness-optimizer`

---

## Скиллы (`~/.claude/skills/`, 104)

**Инженерные основы (18)**
`coding-standards` `api-design` `error-handling` `git-workflow` `github-ops`
`tdd-workflow` `e2e-testing` `ecc-security-review` `security-scan`
`deployment-patterns` `docker-patterns` `database-migrations`
`architecture-decision-records` `hexagonal-architecture` `contract-first`
`codebase-onboarding` `verification-loop` `production-audit`

> `ecc-security-review` переименован из `security-review` — конфликтовал по имени
> со встроенным скиллом харнесса.

**Фронтенд и UI (12)**
`accessibility` `design-system` `frontend-patterns` `frontend-design-direction`
`make-interfaces-feel-better` `motion-foundations` `motion-ui` `react-patterns`
`react-performance` `react-testing` `vite-patterns` `browser-qa`

**Бэкенд, данные, языки (10)**
`backend-patterns` `python-patterns` `python-testing` `golang-patterns`
`rust-patterns` `postgres-patterns` `redis-patterns` `prisma-patterns`
`mcp-server-patterns` `bun-runtime`

**Агентная инженерия (21)**
`agent-self-evaluation` `agent-eval` `agent-harness-construction`
`agent-architecture-audit` `agent-introspection-debugging` `agentic-engineering`
`autonomous-loops` `loop-design-check` `gan-style-harness` `council` `dev-team`
`team-builder` `plan-orchestrate` `context-budget` `config-gc`
`token-budget-advisor` `strategic-compact` `prompt-optimizer` `skill-scout`
`skill-stocktake` `rules-distill`

**Гардрейлы и рабочий процесс (8)**
`gateguard` `delivery-gate` `safety-guard` `santa-method` `eval-harness`
`growth-log` `intent-driven-development` `parallel-execution-optimizer`

**Исследование и утилиты (6)**
`deep-research` `search-first` `documentation-lookup` `click-path-audit`
`regex-vs-llm-structured-text` `seo`

**Оркестрация задач, orch-* (6)**
`orch-pipeline` (движок) `orch-add-feature` `orch-build-mvp` `orch-change-feature`
`orch-fix-defect` `orch-refine-code`

**Стартап (12)**
`product-lens` `brand-discovery` `brand-voice` `market-research`
`competitive-platform-analysis` `benchmark-methodology`
`competitive-report-structure` `investor-materials` `investor-outreach`
`content-engine` `crosspost` `lead-intelligence`

**Автоматизация сайтов (9)**
`data-scraper-agent` `canary-watch` `ui-demo` `opensource-pipeline`
`api-connector-builder` `frontend-slides` `nextjs-turbopack` `dashboard-builder`
`knowledge-ops`

**Память между сессиями (2)**
`ck` (Context Keeper, автор sreedhargs89) `continuous-learning-v2`

---

## Что требует донастройки или не работает

| Что | Статус |
|---|---|
| `continuous-learning-v2` | **Наполовину.** CLI (`scripts/instinct-cli.py`) работает вручную, но автоматическое наблюдение за сессиями требует хуков ECC, а `hooks/hooks.json` жёстко завязан на полную установку плагина (резолвит `CLAUDE_PLUGIN_ROOT` и запускает `scripts/hooks/*.js`, которых нет) |
| `delivery-gate`, `gateguard`, `safety-guard` | Скрипты на месте, в `settings.json` **не** прописаны — работают как инструкции при явном вызове, не как автоматические гейты |
| `ck` | Скрипты `.mjs` требуют Node — есть в `~/.local`. Хук `session-start.mjs` не подключён |
| `deep-research` | Нужны MCP firecrawl / exa — не установлены |
| `documentation-lookup`, агент `docs-lookup` | MCP context7 установлен — работает |
| `browser-qa`, `ui-demo`, `canary-watch`, `e2e-runner` | Playwright MCP установлен — работает |
| `data-scraper-agent` | Нужен ключ Gemini API (бесплатный тариф) и GitHub Actions |

Аудит скриптов: во всём установленном `subprocess`/`spawnSync` вызывают только
`git`, `rm -rf` — исключительно по собственным временным каталогам, сетевых
обращений нет (кроме явного `/instinct-import <url>`, где есть валидация URL).

## Что не бралось

Отраслевое (healthcare/HIPAA, логистика, таможня, энергетика, производство,
складские остатки), сетевое/homelab (VLAN, Pi-hole, WireGuard, Cisco IOS, BGP),
крипто/DeFi/трейдинг, self-referential ECC (`ecc-guide`, `configure-ecc`,
`cost-tracking`, `ito-*`, `nanoclaw-repl`, `openclaw-persona-forge`),
вендорские MCP-обёртки (videodb, fal.ai, Nutrient, Mailtrap, Jira),
семейство `/epic-*` и `/multi-*` (первое завязано на скрипты ECC, второе требует
внешний рантайм `npx ccg-workflow`), а также стеки вне текущего профиля:
Java/Spring/Quarkus, Kotlin/Android, Swift/iOS, C#/.NET, C++, PHP/Laravel, Perl,
Flutter/Dart, Django, HarmonyOS, Angular, Nuxt, NestJS.

Правила (`rules/`) при этом скопированы **все** — они лежат библиотекой и в
контекст не грузятся.

## Обновление

Ручное: заново клонировать репозиторий и скопировать нужные каталоги.
Альтернатива — поставить целиком как плагин (обновления автоматические, хуки
заработают, но в контекст каждой сессии попадут все 284 скилла):

```text
/plugin marketplace add https://github.com/affaan-m/ECC
/plugin install ecc@ecc
```
