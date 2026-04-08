# TASKS.md

# AI Brand Visibility Monitor — Tasks (Pipeline-ready MVP)

---

## 0. Task Rules (обязательные)

Каждая задача:

- реализует ОДНУ функцию
- ≤ ~200 строк изменений (ориентир)
- ссылается на spec
- включает тесты

---

### Обязательные требования к каждой задаче

Каждая задача должна:

1. соответствовать spec  
2. не менять архитектуру  
3. добавить:
   - минимум 1 happy-path тест
   - минимум 1 edge-case тест  

---

## 1. Phase 1 — Project Foundation

---

### T1 — Project structure

Scope:
- создать папки:
  - apps/api
  - workers
  - libs/*
  - docs

Tests:
- не требуются

---

### T2 — DB setup

Scope:
- подключение к Postgres
- базовый connection

Tests:
- test connection (SELECT 1)

---

### T3 — Core models

Scope:
- Brand
- Audit
- Query
- Run
- RawResponse
- ParsedResult
- Score

Tests:
- создание сущностей
- базовые связи

---

### T4 — API: create audit

Spec:
- PRODUCT_SPEC

Scope:
- POST /audits
- валидация input

Tests:
- valid input
- invalid input
- empty brand_name

---

## 2. Phase 2 — Query Layer

---

### T5 — Normalize seed queries

Spec:
- PRODUCT_SPEC

Scope:
- trim
- lowercase
- remove empty

Tests:
- mixed input
- empty strings

---

### T6 — Deduplicate queries

Scope:
- убрать дубликаты
- учитывать case-insensitive

Tests:
- duplicates
- spacing differences

---

### T7 — Apply max_queries cap

Scope:
- ограничение списка

Tests:
- large input
- exact boundary

---

### T8 — Intent tagging

Scope:
- простые правила:
  - best → comparison
  - how → use_case

Tests:
- разные типы запросов

---

## 3. Phase 3 — Provider Layer

---

### T9 — BaseProviderAdapter

Spec:
- PROVIDER_CONTRACT

Scope:
- интерфейс
- DTO

Tests:
- contract shape

---

### T10 — Mock provider

Scope:
- deterministic ответы
- success / error режимы

Tests:
- стабильность output

---

### T11 — Real provider (1)

Scope:
- реализация adapter
- mapping → ProviderResponse

Tests:
- success
- error
- malformed citations

---

## 4. Phase 4 — Execution Layer

---

### T12 — Job model

Scope:
- job entity
- idempotency key

Tests:
- duplicate prevention

---

### T13 — Job scheduler

Spec:
- ARCHITECTURE

Scope:
- query × provider × run

Tests:
- correct combinations
- no duplicates

---

### T14 — Worker execution

Scope:
- вызвать provider
- сохранить RawResponse

Tests:
- success flow
- error flow

---

### T15 — RawResponse storage

Spec:
- ARCHITECTURE

Scope:
- сохранить:
  - raw_answer
  - metadata
  - status

Tests:
- stored correctly
- immutable check

---

## 5. Phase 5 — Parser

---

### T16 — Preprocessing

Spec:
- PARSER_SPEC

Scope:
- lowercase
- split sentences

Tests:
- empty text
- corrupted text

---

### T17 — Brand detection

Scope:
- exact match
- normalized match

Tests:
- positive
- negative

---

### T18 — Mention extraction

Scope:
- позиции
- sentence index

Tests:
- multiple mentions

---

### T19 — Ranking

Scope:
- порядок появления

Tests:
- multiple brands
- single brand

---

### T20 — Competitors

Scope:
- candidate extraction
- frequency

Tests:
- no competitors
- multiple competitors

---

### T21 — Sources

Scope:
- normalize citations
- classify source_type

Tests:
- empty
- malformed citations

---

### T22 — Sentiment

Scope:
- keyword rules

Tests:
- positive
- negative
- neutral

---

### T23 — Recommendation

Scope:
- pattern matching

Tests:
- best
- recommended
- listed

---

### T24 — Ensure full ParsedResult

CRITICAL:

Scope:
- parser всегда возвращает полный объект

Tests:
- null input
- error input
- empty text

---

## 6. Phase 6 — Scoring

---

### T25 — Component metrics

Spec:
- SCORING

Scope:
- visibility
- normalization

Tests:
- edge values

---

### T26 — Final score

Scope:
- формула

Tests:
- exact values
- rounding

---

### T27 — Visibility cap

Scope:
- cap rule

Tests:
- visibility=0
- boundary

---

## 7. Phase 7 — Aggregation

---

### T28 — Query score

Spec:
- ARCHITECTURE

Scope:
- average successful runs

Tests:
- mixed success/error
- no success

---

### T29 — Provider score

Scope:
- average per provider

Tests:
- partial data

---

### T30 — Audit summary

Scope:
- total
- averages
- counts

Tests:
- partial audit
- full audit

---

### T31 — Critical queries

Scope:
- visibility=0
- score<threshold

Tests:
- threshold boundary

---

## 8. Phase 8 — Pipeline

---

### T32 — Pre-commit

Spec:
- DEV_PIPELINE

Scope:
- lint
- fast tests

Tests:
- hook execution

---

### T33 — Pre-push

Scope:
- full test suite

Tests:
- failing test blocks push

---

### T34 — CI

Scope:
- run:
  - unit
  - contract
  - fixture
  - integration
  - e2e (mock)

Tests:
- CI fails on error

---

## 9. Phase 9 — E2E

---

### T35 — Mock E2E pipeline

Scope:
- create audit
- run
- parse
- score
- aggregate

Tests:
- full flow passes

---

## 10. Definition of Done (per task)

Задача завершена, если:

- код соответствует spec  
- есть тесты  
- проходят:
  - pre-commit  
  - pre-push  
- diff review пройден  
- CI проходит  

---

## 11. Global Rules

Запрещено:

- большие задачи  
- изменения без тестов  
- изменение контрактов без обновления spec  
- использование реальных API в тестах  
- “магические fallback”  

---

## 12. Execution Order (важно)

Строго:

1. Phase 1  
2. Phase 2  
3. Phase 3 (mock → real)  
4. Phase 4  
5. Phase 5  
6. Phase 6  
7. Phase 7  
8. Phase 8  
9. Phase 9  

---

## 13. Key Principle

Каждая задача должна быть:

**маленькой, проверяемой, безопасной**