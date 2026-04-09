# SCORING.md

# AI Brand Visibility Monitor — Scoring Specification (MVP)

---

## 1. Purpose

Scoring Engine преобразует `ParsedResult` в:

- component metrics
- final_score

Scoring НЕ:
- читает raw ответы
- вызывает provider
- выполняет parsing

Scoring работает только с детерминированным входом.

---

## 2. Design Principles

### 2.1 Determinism
Одинаковый input → одинаковый output

---

### 2.2 Isolation
Scoring зависит только от `ParsedResult`

---

### 2.3 Bounded outputs
Все значения строго ограничены диапазонами

---

### 2.4 Simplicity
Никаких сложных моделей, только фиксированные формулы

---

### 2.5 Testability
Каждая метрика тестируется отдельно

---

## 3. Input Contract

## 3.1 ScoringInput

```json
{
  "brand_detected": false,
  "brand_position_rank": null,
  "prominence_score": 0,
  "sentiment": 0,
  "recommendation_score": 0,
  "source_quality_score": 0.5
}