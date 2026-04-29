# PARSER_SPEC.md

# AI Brand Visibility Monitor — Parser Specification (MVP)

---

## 1. Purpose

Parser преобразует `ProviderResponse` в структурированный `ParsedResult`.

Parser НЕ:
- вызывает AI
- считает финальный score
- принимает продуктовые решения

Parser — детерминированный слой извлечения сигналов.

---

## 2. Design Principles

### 2.1 Determinism
Одинаковый вход → одинаковый выход.

---

### 2.2 Failure-safe
Parser никогда не должен падать.

---

### 2.3 Provider-agnostic
Parser не должен зависеть от конкретного провайдера.

---

### 2.4 Re-runnable
Parser должен работать только на сохранённых данных.

---

### 2.5 Minimal intelligence
Rule-based логика, без ML и LLM.

---

## 3. Input Contract

## 3.1 ParserInput

```json
{
  "brand_name": "string",
  "brand_domain": "string | null",

  "query": "string",

  "provider_response": {
    "status": "string",
    "raw_answer": "string | null",
    "citations": []
  }
}