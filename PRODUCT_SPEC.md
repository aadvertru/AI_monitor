# PRODUCT_SPEC.md

# AI Brand Visibility Monitor — Product Specification (MVP)

## 1. Purpose

AI Brand Visibility Monitor — инструмент для аудита того, как бренд представлен в ответах AI-провайдеров по релевантным запросам.

Система отвечает на вопросы:

- появляется ли бренд в ответах AI
- насколько заметно он представлен
- какие конкуренты появляются рядом или вместо него
- какие источники используются в ответах
- как это выглядит в агрегированном виде по провайдеру, запросу и аудиту

Система не является классическим SEO-инструментом и не анализирует SERP как основной объект.

---

## 2. MVP Goal

MVP должен позволять выполнить один полный audit cycle:

1. принять бренд и настройки аудита
2. получить рабочий набор запросов
3. выполнить прогоны по выбранным провайдерам
4. сохранить сырые результаты
5. извлечь структурированные сигналы
6. посчитать score
7. построить summary и экспорт

---

## 3. Primary User Problem

Бренд может иметь хорошую веб-видимость, но:
- не попадать в AI-ответы
- проигрывать конкурентам
- попадать в ответ в слабой позиции
- зависеть от источников, которые не контролируются брендом

Пользователю нужен способ измерять это системно и воспроизводимо.

---

## 4. Core Object Model

### 4.1 Primary object
Основная сущность системы — `Audit`.

`Audit` = одна завершённая или частично завершённая проверка бренда по:
- набору запросов
- набору провайдеров
- правилам парсинга и scoring
- заданным настройкам запуска

### 4.2 Supporting objects
MVP опирается на следующие логические объекты:
- `Brand`
- `Audit`
- `Query`
- `Run`
- `RawResponse`
- `ParsedResult`
- `Score`
- `Summary`

Это не схема БД, а продуктовая модель.

---

## 5. Scope

## 5.1 In Scope

MVP включает:

- создание аудита
- валидацию входных данных
- приём brand input
- приём seed queries или генерацию queries
- нормализацию и дедупликацию queries
- запуск по 1–2 AI-провайдерам
- multi-run execution в диапазоне 1–5
- сохранение raw responses
- rule-based parsing
- score calculation по фиксированным правилам
- summary по аудиту
- экспорт результатов
- обязательные automated tests для core contracts

---

## 5.2 Out of Scope

MVP не включает:

- сложные multi-turn сценарии глубже 1 follow-up
- agentic workflows
- автоматическую генерацию рекомендаций по контенту
- сложный competitor graph
- always-on / scheduled monitoring
- billing
- multi-tenant SaaS
- публичное API для клиентов
- поддержку большого числа провайдеров
- ML-heavy / embedding-heavy parsing
- самостоятельную интерпретацию бизнес-стратегии бренда

---

## 6. Inputs

## 6.1 Required input

### Brand input
- `brand_name: string`

### Audit settings
- `providers: string[]`
- `runs_per_query: integer`

---

## 6.2 Optional input

### Brand metadata
- `brand_domain: string | null`
- `brand_description: string | null`

### Query input
- `seed_queries: string[] | null`

### Audit settings
- `language: string | null`
- `country: string | null`
- `locale: string | null`
- `max_queries: integer | null`
- `enable_query_expansion: boolean`
- `enable_source_intelligence: boolean`
- `follow_up_depth: 0 | 1`

---

## 6.3 Input validation rules

### brand_name
- must be string
- must not be empty after trim
- max length must be bounded by implementation
- leading/trailing whitespace must be removed

### providers
- must be array
- must contain at least one supported provider
- duplicates must be removed during normalization

### runs_per_query
- integer only
- allowed range: 1..5

### seed_queries
- if present, must be array of strings
- empty strings must be removed
- duplicates must be removed

### brand_domain
- if present, may be invalid
- invalid domain must not crash audit creation
- invalid domain may be stored as rejected/ignored normalized value

### follow_up_depth
- allowed values: 0 or 1 only

### max_queries
- if present, must be integer > 0

---

## 6.4 Input edge cases

### Empty brand name
- audit creation must fail with validation error

### Unsupported provider code
- audit creation must fail with validation error

### Partially valid provider list
- invalid provider entries must cause validation failure for the request
- request must not be silently downgraded

### Empty seed_queries array
- treated as absent input
- query generation fallback is used

### Mixed valid/invalid seed queries
- invalid entries are removed if sanitizable
- if no valid queries remain, query generation fallback is used

### Oversized seed query list
- input is normalized
- hard cap is applied using `max_queries` or system default

### Missing optional locale settings
- defaults are applied by system normalization

### Very large brand_description
- must be truncated or rejected by bounded rules
- must not be allowed to destabilize generation stage

---

## 7. Outputs

## 7.1 Primary output

Основной результат — таблица по комбинациям:

`query × provider × run`

Минимальные поля строки:

- `audit_id`
- `query`
- `provider`
- `run_number`
- `run_status`
- `visible_brand`
- `brand_position_rank`
- `prominence_score`
- `sentiment`
- `recommendation_score`
- `source_quality_score`
- `final_score`
- `competitors`
- `sources`
- `raw_answer_ref`

---

## 7.2 Output field constraints

### run_status
Allowed values:
- `success`
- `error`
- `timeout`
- `rate_limited`
- `unsupported`
- `skipped`

### visible_brand
- boolean or normalized 0/1

### brand_position_rank
- integer >= 1
- null if brand not found

### prominence_score
- bounded to [0,1]

### sentiment
- bounded to [-1,1]

### recommendation_score
- bounded to [0,1]

### source_quality_score
- bounded to [0,1]

### final_score
- bounded to [0,1]

### competitors
- list, possibly empty

### sources
- list, possibly empty

### raw_answer_ref
- reference to stored raw response
- must exist for every executed run, even if raw text is empty

---

## 7.3 Aggregated output

MVP must produce:

### Critical queries
Queries where:
- brand is absent
- or score is below configured threshold

### Top competitors
Competitors most frequently appearing near or instead of the brand

### Top sources
Most frequent cited or extracted sources

### Provider summary
Average score and completion stats per provider

### Audit summary
At minimum:
- total queries
- total runs
- completion ratio
- visibility ratio
- average score
- count of critical queries

---

## 7.4 Output edge cases

### Provider returns hard error
- run must be recorded
- audit must continue where possible

### Provider returns empty raw answer
- run must still be recorded
- parser must return empty-safe result

### Provider returns malformed citation data
- malformed citation entries must be ignored or normalized
- parsing must not fail the whole run

### No sources available
- sources = []
- source quality fallback must be applied

### All runs fail for one provider
- provider summary must still be generated
- audit may finish as `partial`

### All runs fail for all providers
- audit must finish as `failed` or `partial` by explicit rules
- result must remain inspectable

---

## 8. Main flow

## Step 1. Create audit
User submits brand input and settings.

## Step 2. Normalize input
System validates and normalizes:
- brand data
- provider list
- run settings
- query-related input

## Step 3. Prepare queries
System:
- accepts seed queries if present
- otherwise generates query set
- normalizes and caps query volume

## Step 4. Schedule execution
System creates execution jobs for each:
- query
- provider
- run number

## Step 5. Execute providers
Each job:
- calls provider adapter
- stores raw response
- stores execution metadata

## Step 6. Parse response
System extracts:
- brand presence
- brand position
- competitor candidates
- sources
- parser signals

## Step 7. Score result
System calculates:
- component metrics
- final score

## Step 8. Aggregate audit
System builds:
- per-run results
- per-query summaries
- per-provider summary
- audit summary

## Step 9. Export / inspect
User can inspect results and export them.

---

## 9. Functional requirements

## 9.1 Audit lifecycle
System must support:
- create audit
- validate audit input
- run audit
- inspect audit status
- inspect audit results
- inspect audit summary

## 9.2 Query preparation
System must support:
- seed query intake
- generated query fallback
- normalization
- deduplication
- capping of query count

## 9.3 Provider execution
System must support:
- provider execution by adapter contract
- retries for retryable failures
- status recording for each run
- persistence of raw response and metadata

## 9.4 Parsing
System must support:
- deterministic parser execution
- empty-safe parsing
- normalized parser output
- re-run parsing without re-calling provider

## 9.5 Scoring
System must support:
- deterministic score calculation
- separate component metrics
- re-run scoring without re-calling provider

## 9.6 Reporting
System must support:
- result table generation
- audit summary generation
- export in at least one machine-readable format

---

## 10. Non-functional requirements

### Determinism
Parser and scoring must be deterministic for the same input.

### Re-runnability
Raw responses must allow re-running parser and scoring without re-executing providers.

### Failure isolation
Failure of one run or one provider must not automatically fail the whole audit.

### Observability
All critical transitions and failures must be logged.

### Testability
Each contract boundary must be testable in isolation.

### Small-task readiness
The system must be decomposable into small implementation tasks suitable for Codex.

### Reviewability
The system structure must support git-diff review by Claude.

---

## 11. Success criteria

MVP is successful if:

1. audit can be created through validated input
2. at least one provider works end-to-end
3. raw responses are stored for all executed runs
4. parser can be re-run on stored data
5. scoring can be re-run on stored data
6. audit summary is produced without manual intervention
7. at least 100 run executions can complete without pipeline collapse
8. pre-commit, pre-push and CI gates can validate core quality rules

---

## 12. Failure conditions

MVP is not ready if:

- audit cannot complete or partially complete in a controlled way
- raw responses are not stored
- parser and scoring cannot be run independently
- final score cannot be traced back to parser inputs
- one bad provider breaks whole audit execution
- tasks are too large to be safely implemented/reviewed through Codex pipeline
- core tests are missing or unstable

---

## 13. Definition of done

MVP is done when:

- product spec is agreed
- architecture is agreed
- contracts are agreed
- development pipeline is agreed
- at least one provider is integrated
- one end-to-end audit works
- core tests exist and pass locally
- pre-push and CI checks pass
- results are inspectable and exportable

---

## 14. Constraints

- no unnecessary abstractions
- no speculative future-proofing
- no broad provider support in MVP
- no deep multi-turn reasoning in MVP
- no parser/scoring dependency on provider-specific business logic
- no code generation tasks larger than reviewable units

---

## 15. Assumptions

- at least one usable provider API is available
- raw provider output can be persisted
- query generation can be simple in MVP
- UI may remain minimal
- fixture-based testing can be used for parser and scoring

If one of these assumptions fails, MVP must be reduced in scope instead of expanded in complexity.