# PROVIDER_CONTRACT.md

# AI Brand Visibility Monitor — Provider Contract (MVP)

---

## 1. Purpose

Provider Contract определяет единый интерфейс взаимодействия с AI-провайдерами.

Контракт нужен для:

- изоляции внешних API
- унификации ответов
- обеспечения тестируемости
- предотвращения утечки provider-specific логики в ядро

---

## 2. Design Principles

### 2.1 Isolation
Provider adapter изолирует:
- API вызовы
- формат ответа
- ошибки

---

### 2.2 Deterministic output shape
Независимо от провайдера, выход всегда одинакового формата.

---

### 2.3 No business logic
Adapter НЕ:
- считает scoring
- извлекает конкурентов
- интерпретирует бизнес-смысл

---

### 2.4 Failure-safe
Любая ошибка возвращается в нормализованном виде.

---

### 2.5 Testability
Adapter должен быть тестируем:
- через mock responses
- через contract tests

---

## 3. Execution Model

Один вызов adapter =

```text
(query × provider × run_number)