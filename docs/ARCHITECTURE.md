# AI Brand Visibility Monitor — Architecture (MVP)

---

## 1. Purpose

Архитектура определяет:

- как выполняется audit pipeline
- как разделена ответственность между модулями
- какие данные и в каком виде передаются
- какие гарантии (invariants) система обязана соблюдать

---

## 2. Architectural Goals

Система должна:

- выполнять audit end-to-end
- быть устойчивой к частичным сбоям
- поддерживать повторный анализ (re-runnability)
- быть разбиваемой на маленькие задачи (Codex)
- быть проверяемой через diff (Claude)
- быть покрываемой тестами (CI)

---

## 3. High-Level Structure

Система разделена на 4 слоя:

1. Control Layer  
2. Execution Layer  
3. Analysis Layer  
4. Storage Layer  

---

## 4. Layer Responsibilities

---

## 4.1 Control Layer

### Компоненты
- API  
- Orchestrator  
- Job Scheduler  

---

### API

Отвечает за:

- создание audit  
- валидацию input  
- запуск audit  
- получение статуса и результатов  

НЕ делает:

- provider calls  
- parsing  
- scoring  

---

### Orchestrator

Отвечает за:

- нормализацию входа  
- запуск query generation  
- запуск scheduler  
- отслеживание выполнения  
- финализацию audit  

---

### Job Scheduler

Создаёт jobs:
query × provider × run_number
Обязанности:

- учитывать max_queries  
- учитывать runs_per_query  
- избегать дублирования  

---

## 4.2 Execution Layer

---

### Worker

Отвечает за:

- выполнение job  
- вызов provider adapter  
- сохранение RawResponse  

НЕ делает:

- parsing  
- scoring  

---

### Provider Adapter

Контракт: см. PROVIDER_CONTRACT.md  

Отвечает за:

- вызов внешнего API  
- нормализацию ответа  
- нормализацию ошибок  

НЕ делает:

- бизнес-логику  
- хранение данных  

---

## 4.3 Analysis Layer
re-run parser
re-run scoring
без повторных provider вызовов
---

### Parser

Контракт: см. PARSER_SPEC.md  

Отвечает за:

- извлечение сигналов  
- нормализацию данных  

Гарантия:

- всегда возвращает полный ParsedResult  

---

### Scoring

Контракт: см. SCORING.md  

Отвечает за:

- вычисление component metrics  
- вычисление final_score  

---

### Aggregation

Отвечает за:

- агрегирование данных  
- построение summary  

---

## 4.4 Storage Layer

---

### Entities

- Brand  
- Audit  
- Query  
- Run  
- RawResponse  
- ParsedResult  
- Score  

---

### Data Separation (Critical)

#### Raw Layer
- raw_answer  
- citations  
- provider metadata  
- provider status  
- error object  
- request snapshot  

#### Parsed Layer
- parsed_result  

#### Score Layer
- score  

---

### Purpose of Separation

Обеспечить:

---

## 5. End-to-End Flow

1. Create audit  
2. Normalize input  
3. Generate queries  
4. Schedule jobs  
5. Execute providers  
6. Store RawResponse  
7. Parse  
8. Score  
9. Aggregate  

---

## 6. Data Flow
Audit → Queries → Jobs
→ Provider → RawResponse
→ Parser → ParsedResult
→ Scoring → Score
→ Aggregation → Summary
---

## 7. State Model

---

## 7.1 Audit States

| State      | Description |
|------------|------------|
| created    | audit создан |
| running    | выполняется |
| partial    | часть run упала |
| completed  | все run успешны |
| failed     | все run упали |

---

## 7.2 Audit Transitions
created → running
running → completed
running → partial
running → failed


---

## 7.3 Run States

| State        | Description |
|--------------|------------|
| pending      | ожидает |
| success      | успешно |
| error        | ошибка |
| timeout      | таймаут |
| rate_limited | лимит |

---

## 7.4 Run Transitions
pending → success
pending → error
pending → timeout
pending → rate_limited


---

## 8. Invariants (Critical)

Следующие правила НЕ МОГУТ нарушаться:

---

### Provider Layer

- всегда возвращает ProviderResponse  
- не бросает исключения наружу  

---

### RawResponse

- сохраняется для каждого run  
- immutable после записи  

---

### Parser

- никогда не падает  
- всегда возвращает полный ParsedResult  

---

### ParsedResult

- не содержит null (кроме brand_position_rank)  
- все поля присутствуют  

---

### Scoring

- всегда возвращает score  
- final_score ∈ [0,1]  

---

### Run

- всегда записывается  
- всегда имеет статус  

---

### Audit

- не может зависнуть  
- всегда завершён одним из финальных статусов  

---

## 9. RawResponse Contract

Каждый run должен сохранять:

- request snapshot  
- raw_answer  
- citations (raw + normalized)  
- provider status  
- response_time  
- error object  
- provider metadata  

---

## 10. Aggregation Contract

---

### 10.1 Query Score

---

## 8. Invariants (Critical)

Следующие правила НЕ МОГУТ нарушаться:

---

### Provider Layer

- всегда возвращает ProviderResponse  
- не бросает исключения наружу  

---

### RawResponse

- сохраняется для каждого run  
- immutable после записи  

---

### Parser

- никогда не падает  
- всегда возвращает полный ParsedResult  

---

### ParsedResult

- не содержит null (кроме brand_position_rank)  
- все поля присутствуют  

---

### Scoring

- всегда возвращает score  
- final_score ∈ [0,1]  

---

### Run

- всегда записывается  
- всегда имеет статус  

---

### Audit

- не может зависнуть  
- всегда завершён одним из финальных статусов  

---

## 9. RawResponse Contract

Каждый run должен сохранять:

- request snapshot  
- raw_answer  
- citations (raw + normalized)  
- provider status  
- response_time  
- error object  
- provider metadata  

---

## 10. Aggregation Contract

---

### 10.1 Query Score
average(final_score of successful runs)

---

### 10.2 Provider Score


average(all successful runs per provider)
---

### 10.3 Audit Score
average(query_scores)


---

### 10.4 Critical Queries

Query считается критическим если:

- visibility == 0  
ИЛИ  
- final_score < threshold (default = 0.3)  

---

## 11. Failure Handling

---

### Provider Failure

- run.status = error  
- audit продолжается  

---

### Partial Audit

- часть run упала  
- audit.status = partial  

---

### Total Failure

- все run упали  
- audit.status = failed  

---

### Parser Failure

- возвращается safe result  
- ошибка логируется  

---

### Scoring Failure

- score не записывается  
- ошибка логируется  

---

## 12. Retry Policy

Retry выполняется только если:

- timeout  
- rate_limited  
- temporary error  

---

Ограничение:

- максимум 2–3 попытки  

---

## 13. Idempotency

Уникальный ключ:
audit_id + query_id + provider + run_number


---

## 14. Concurrency

- jobs выполняются параллельно  
- порядок выполнения не гарантирован  
- worker масштабируем  

---

## 15. Contract Boundaries

---

- API → Orchestrator  
- Orchestrator → QueryGen  
- Orchestrator → Scheduler  
- Worker → Provider  
- Provider → Worker  
- Worker → Storage  
- Parser → Storage  
- Scoring → Storage  

---

## 16. Testability

Каждый слой должен тестироваться отдельно:

- QueryGen — unit tests  
- Provider — contract tests  
- Parser — fixture tests  
- Scoring — deterministic tests  
- Aggregation — unit tests  

---

## 17. Constraints

- не добавлять лишние абстракции  
- не смешивать слои  
- parser не зависит от provider  
- scoring не зависит от raw ответа  

---

## 18. MVP Constraints

- максимум 1–2 providers  
- простой parser  
- простой scoring  
- минимальный UI  

---

## 19. Success Criteria

Архитектура корректна, если:

1. можно добавить provider без изменения ядра  
2. можно пересчитать parser/scoring без provider calls  
3. система устойчива к сбоям  
4. каждый слой тестируется  
5. задачи можно дробить до уровня Codex  

---

## 20. Key Principle

Архитектура должна обеспечивать:

**предсказуемость > гибкость**