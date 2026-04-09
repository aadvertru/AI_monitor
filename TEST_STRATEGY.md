# TEST_STRATEGY.md

# AI Brand Visibility Monitor — Test Strategy (MVP)

---

## 1. Purpose

Эта стратегия определяет:

- что тестируется
- на каком уровне тестируется
- какие тесты обязательны для MVP
- какие проверки должны запускаться локально и в CI

Цель тестирования MVP:

- предотвратить ложные результаты аудита
- предотвратить поломку pipeline
- гарантировать воспроизводимость parser/scoring
- сделать изменения безопасными для review-driven development

---

## 2. Testing Principles

### 2.1 Test contracts, not assumptions
Тестируются формальные контракты модулей:
- input
- output
- границы значений
- edge cases

---

### 2.2 Determinism first
Максимальный приоритет:
- parser
- scoring
- aggregation rules

Если эти модули нестабильны, продукт становится недостоверным.

---

### 2.3 Small-test bias
Предпочтение:
- unit tests
- contract tests
- fixture tests

а не тяжёлым интеграционным тестам.

---

### 2.4 Failure-safe behavior must be testable
Каждый слой должен иметь тесты на:
- пустые данные
- битые данные
- частичный отказ
- частично валидный вход

---

### 2.5 CI must enforce core quality
CI должен блокировать merge/push, если ломаются:
- контракты
- parser/scoring
- критические pipeline проверки

---

## 3. Test Pyramid for MVP

Используем упрощённую пирамиду:

### Level 1 — Unit tests
Проверка отдельных функций и правил.

### Level 2 — Contract tests
Проверка, что модуль соблюдает свой формальный контракт.

### Level 3 — Fixture tests
Проверка parser/scoring на заранее зафиксированных примерах.

### Level 4 — Thin integration tests
Проверка связки нескольких модулей без сложной инфраструктуры.

### Level 5 — One end-to-end happy-path test
Один минимальный e2e сценарий на mock provider.

---

## 4. Test Scope by Module

---

## 4.1 Input Validation / Audit Creation

### What to test
- пустой brand_name
- invalid provider list
- duplicate providers
- invalid runs_per_query
- empty and mixed seed_queries
- max_queries validation
- follow_up_depth validation

### Required test types
- unit tests
- API-level validation tests

### Done criteria
- невалидный input не проходит
- валидный input нормализуется предсказуемо

---

## 4.2 Query Generation

### What to test
- seed query ingestion
- normalization
- deduplication
- capping by max_queries
- intent tagging
- fallback generation when seed queries absent

### Edge cases
- empty list
- duplicates with spacing/case differences
- extremely long queries
- mixed valid and invalid queries

### Required test types
- unit tests
- fixture tests for normalized query sets

### Done criteria
- список запросов воспроизводим
- одинаковый input → одинаковый output

---

## 4.3 Provider Adapters

### What to test
- success response normalization
- empty response handling
- error mapping
- malformed citation normalization
- capability declarations
- mock mode behavior

### Edge cases
- timeout
- rate limit
- unsupported locale
- null fields in provider payload
- partial citation objects
- provider-specific junk fields

### Required test types
- unit tests
- contract tests
- mock provider tests

### Done criteria
- adapter всегда возвращает ProviderResponse
- необработанные исключения наружу не уходят

---

## 4.4 Worker / Execution Pipeline

### What to test
- job creation per query/provider/run
- idempotency key behavior
- retryable vs non-retryable flows
- raw response persistence
- partial failure behavior

### Edge cases
- duplicate scheduling attempts
- provider error after partial execution
- timeout followed by retry success
- all jobs for one provider fail

### Required test types
- thin integration tests

### Done criteria
- jobs не дублируются бесконтрольно
- retry policy работает по правилам
- raw response сохраняется всегда для executed run

---

## 4.5 Parser

### What to test
- safe empty result behavior
- brand detection
- mention extraction
- brand rank extraction
- competitor extraction
- source normalization
- source classification
- sentiment extraction
- recommendation extraction
- prominence calculation input signals

### Edge cases
- status != success
- raw_answer = null
- raw_answer = ""
- malformed unicode text
- overlapping matches
- no competitors
- no citations
- malformed citations
- brand mentioned via domain only
- conflicting sentiment cues

### Required test types
- unit tests
- fixture tests
- edge-case tests

### Done criteria
- parser never throws
- parser output schema always stable
- same input always yields same ParsedResult

---

## 4.6 Scoring

### What to test
- visibility calculation
- clamping rules
- sentiment normalization
- recommendation normalization
- source quality normalization
- final formula
- visibility cap rule
- rounding rules
- aggregation rules

### Edge cases
- visibility = 0
- sentiment = -1 / 1
- out-of-range inputs
- partial parsed input
- null rank
- no successful runs in aggregation

### Required test types
- unit tests
- fixture tests

### Done criteria
- score is deterministic
- final score bounded to [0,1]
- cap rule always applied

---

## 4.7 Aggregation / Reporting

### What to test
- average per query
- average per provider
- audit summary generation
- critical query selection
- competitor frequency aggregation
- source frequency aggregation
- export data shape

### Edge cases
- no successful runs
- partial audit
- empty sources across entire audit
- export with zero successful rows

### Required test types
- unit tests
- snapshot-like tests for summary output

### Done criteria
- summary строится без падения
- summary корректен на partial data

---

## 4.8 API Layer

### What to test
- health endpoints
- create audit
- get audit
- run audit
- fetch summary/results
- validation errors

### Required test types
- API integration tests

### Done criteria
- API стабильно обрабатывает валидные/невалидные запросы

---

## 5. Required Test Suites

Для MVP обязательны следующие наборы тестов:

### 5.1 Unit test suite
Обязателен для:
- query normalization
- provider normalization helpers
- parser rules
- scoring rules
- aggregation rules

---

### 5.2 Contract test suite
Обязателен для:
- ProviderResponse contract
- ParsedResult contract
- Score output contract

---

### 5.3 Fixture test suite
Обязателен для:
- parser
- scoring

Fixtures должны быть:
- небольшими
- читаемыми
- зафиксированными в репозитории

---

### 5.4 Thin integration suite
Обязателен для:
- orchestrator → scheduler
- worker → provider → raw storage
- parser → scoring pipeline

---

### 5.5 Single e2e suite
Один happy-path сценарий:
- create audit
- generate queries
- run mock provider
- parse
- score
- aggregate

---

## 6. Fixtures Strategy

### 6.1 Purpose
Fixtures нужны, чтобы тестировать parser/scoring на стабильных входах.

---

### 6.2 Fixture types

#### Parser fixtures
Содержат:
- brand input
- query
- provider response
- expected ParsedResult

#### Scoring fixtures
Содержат:
- ParsedResult
- expected Score

#### Provider fixtures
Содержат:
- raw provider payload
- expected ProviderResponse

---

### 6.3 Fixture rules
- хранить в читаемом формате
- имена файлов должны быть предсказуемыми
- один fixture = один кейс
- fixtures не должны зависеть от сети

---

## 7. Mocking Strategy

### 7.1 What may be mocked
- provider API calls
- retries
- queue internals (частично)
- timeouts

---

### 7.2 What should not be mocked in core tests
- parser logic
- scoring logic
- aggregation formulas

---

### 7.3 Mock provider
Для MVP обязательно иметь deterministic mock provider, который:
- всегда возвращает валидный ProviderResponse
- умеет success/error/empty modes
- используется в e2e tests

---

## 8. Test Data Quality Rules

Тестовые данные должны включать:

- корректные кейсы
- пустые кейсы
- частично битые кейсы
- длинные строки
- mixed-valid data
- provider error cases

---

## 9. Pre-commit Checks

Pre-commit должен запускать быстрые проверки:

- formatting
- lint
- type checks (если включены)
- fast unit tests for touched modules

### Goal
Остановить очевидно плохой commit до review.

---

## 10. Pre-push Checks

Pre-push должен запускать:

- full test suite для core модулей
- contract tests
- fixture tests
- thin integration tests

### Goal
Не пускать в remote код, который ломает core behavior.

---

## 11. CI Checks

CI должен запускать:

- install/build sanity
- lint
- unit tests
- contract tests
- fixture tests
- thin integration tests
- one e2e happy-path test

---

### CI must fail if:
- ломается любой contract test
- parser/scoring становятся недетерминированными
- падает e2e happy-path
- падают обязательные quality checks

---

## 12. Review-Gated Development Rules

Каждая задача из `TASKS.md` должна сопровождаться:

1. описанием test impact
2. новыми или обновлёнными тестами
3. объяснением, что именно проверено

---

### Claude review should verify:
- есть ли тесты на новый контракт
- не сломаны ли edge cases
- нет ли “silent fallback” без тестов
- не изменилось ли поведение без обновления spec

---

## 13. Minimum Coverage Expectations

Формальный процент покрытия не является главной метрикой.

Для MVP обязательнее:
- coverage по критическим модулям, а не глобальный %
- наличие tests на каждый documented edge case

---

### Critical modules requiring strong coverage
- parser
- scoring
- provider normalization
- query normalization
- aggregation core

---

## 14. Failure Conditions for Test Strategy

Стратегия считается нарушенной, если:

- parser меняется без fixture tests
- scoring меняется без formula tests
- provider adapter добавляется без contract tests
- e2e зависит от реального внешнего API
- важные edge cases остаются непроверенными
- CI пропускает поломку core contracts

---

## 15. Definition of Done for Testing

Фича или модуль считаются готовыми, если:

- есть тесты на happy path
- есть тесты на ключевые edge cases
- соблюдён соответствующий контракт
- локальные проверки проходят
- pre-push проходит
- CI проходит

---

## 16. MVP Constraints

- не строить тяжёлую интеграционную матрицу
- не использовать сеть в parser/scoring tests
- не завязывать e2e на реальные provider APIs
- не раздувать число тестовых слоёв
- не подменять contract tests ручной проверкой

---

## 17. Key Principle

Тесты в этом проекте нужны не для “процента покрытия”.

Они нужны для того, чтобы система:
- не врала
- не деградировала незаметно
- не ломалась при маленьких изменениях