import { AlertTriangle, ChevronDown, X } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "../../components/ui/Button";
import type {
  AnswerMatrixCell,
  AnswerMatrixCellStatus,
  AnswerMatrixColumn,
  AnswerMatrixResponse,
  AnswerMatrixRow,
  AuditStatus,
  EvaluationVerdict,
  ProviderDiagnostic,
  SCDLLevel,
  SeedQueryType,
} from "../../lib/api/types";
import { ProviderDiagnostics, ProviderIssueText } from "./ProviderDiagnostics";
import { useAuditAnswerMatrix } from "./useAuditAnswerMatrix";

type FilterValue = "all" | string;

type MatrixFilters = {
  level: FilterValue;
  aiFamily: FilterValue;
  model: FilterValue;
  verdict: FilterValue;
  queryType: FilterValue;
  status: FilterValue;
};

type SelectedCell = {
  row: AnswerMatrixRow;
  column: AnswerMatrixColumn;
  cell: AnswerMatrixCell;
};

const defaultFilters: MatrixFilters = {
  level: "all",
  aiFamily: "all",
  model: "all",
  verdict: "all",
  queryType: "all",
  status: "all",
};

const unsafePattern =
  /api_key|authorization|headers|raw_response|raw_prompt|raw_tool_result|raw_annotations|stack_trace|traceback|openai_api_key|openrouter_api_key|sk-/i;

const cellStatuses: AnswerMatrixCellStatus[] = [
  "completed",
  "partial",
  "failed",
  "processing",
  "not_run",
  "missing",
];

const verdicts: EvaluationVerdict[] = [
  "correct",
  "partial",
  "incorrect",
  "unknown",
  "not_applicable",
];

function safeText(value: unknown, fallback = "") {
  if (typeof value !== "string" || unsafePattern.test(value)) {
    return fallback;
  }
  return value;
}

function uniqueValues(values: Array<string | null | undefined>) {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value))));
}

function optionLabel(value: string | null | undefined, fallback = "N/A") {
  return safeText(value, fallback) || fallback;
}

function columnModelValue(column: AnswerMatrixColumn) {
  return column.model_id ?? column.label;
}

function cellPassesFilters(cell: AnswerMatrixCell | undefined, filters: MatrixFilters) {
  if (!cell) {
    return filters.status === "all" || filters.status === "missing";
  }
  if (filters.status !== "all" && cell.status !== filters.status) {
    return false;
  }
  if (filters.verdict === "all") {
    return true;
  }
  return cell.evaluation?.verdict === filters.verdict;
}

function visibleColumns(columns: AnswerMatrixColumn[], filters: MatrixFilters) {
  return columns.filter((column) => {
    if (filters.level !== "all" && column.level !== filters.level) {
      return false;
    }
    if (filters.aiFamily !== "all" && column.ai_family !== filters.aiFamily) {
      return false;
    }
    if (filters.model !== "all" && columnModelValue(column) !== filters.model) {
      return false;
    }
    return true;
  });
}

function rowCellsByTarget(row: AnswerMatrixRow) {
  return new Map(row.cells.map((cell) => [cell.target_id, cell]));
}

function visibleRows(
  rows: AnswerMatrixRow[],
  columns: AnswerMatrixColumn[],
  filters: MatrixFilters,
) {
  return rows.filter((row) => {
    if (filters.queryType !== "all" && (row.query_type ?? "unknown") !== filters.queryType) {
      return false;
    }

    const cells = rowCellsByTarget(row);
    return columns.some((column) => cellPassesFilters(cells.get(column.target_id), filters));
  });
}

function matrixHasData(matrix: AnswerMatrixResponse) {
  return matrix.columns.length > 0 && matrix.rows.length > 0;
}

function hasOpenRouterExperimentalL2(columns: AnswerMatrixColumn[]) {
  return columns.some((column) => column.level === "L2" && column.gateway_l2_experimental);
}

function statusClass(status: AnswerMatrixCellStatus) {
  switch (status) {
    case "completed":
      return "border-emerald-200 bg-emerald-50 text-emerald-800";
    case "partial":
      return "border-amber-200 bg-amber-50 text-amber-800";
    case "failed":
      return "border-red-200 bg-red-50 text-red-800";
    case "processing":
      return "border-blue-200 bg-blue-50 text-blue-800";
    case "not_run":
    case "missing":
      return "border-border bg-muted text-subtle";
  }
}

function verdictClass(verdict: EvaluationVerdict) {
  switch (verdict) {
    case "correct":
      return "border-emerald-200 bg-emerald-50 text-emerald-800";
    case "partial":
      return "border-amber-200 bg-amber-50 text-amber-800";
    case "incorrect":
      return "border-red-200 bg-red-50 text-red-800";
    case "unknown":
    case "not_applicable":
      return "border-border bg-muted text-subtle";
  }
}

function FieldSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: FilterValue;
  options: Array<{ value: FilterValue; label: string }>;
  onChange: (value: FilterValue) => void;
}) {
  return (
    <label className="grid gap-1 text-sm font-medium text-ink">
      <span>{label}</span>
      <select
        className="h-10 rounded-md border border-border bg-white px-3 text-sm text-ink outline-none transition-colors focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function MatrixStatusBadge({ status }: { status: AnswerMatrixCellStatus }) {
  const { t } = useTranslation("results");
  return (
    <span
      className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-semibold ${statusClass(
        status,
      )}`}
    >
      {t(`matrix.status.${status}`)}
    </span>
  );
}

function VerdictBadge({ verdict }: { verdict: EvaluationVerdict }) {
  const { t } = useTranslation("results");
  return (
    <span
      className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-semibold ${verdictClass(
        verdict,
      )}`}
    >
      {t(`matrix.verdict.${verdict}`)}
    </span>
  );
}

function MissingCell() {
  const { t } = useTranslation("results");
  return (
    <div className="min-h-32 rounded-md border border-dashed border-border bg-muted p-3 text-sm text-subtle">
      <MatrixStatusBadge status="missing" />
      <p className="mt-3">{t("matrix.cell.missing")}</p>
    </div>
  );
}

function MatrixCell({
  cell,
  row,
  column,
  onSelect,
}: {
  cell: AnswerMatrixCell;
  row: AnswerMatrixRow;
  column: AnswerMatrixColumn;
  onSelect: (selection: SelectedCell) => void;
}) {
  const { t } = useTranslation("results");
  const answerExcerpt = safeText(cell.answer_excerpt, "");
  const rationale = safeText(cell.evaluation?.rationale, "");
  const providerMessage = safeText(cell.provider_error?.message, "");

  return (
    <div className="min-h-32 rounded-md border border-border bg-white p-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <MatrixStatusBadge status={cell.status} />
        {cell.evaluation ? <VerdictBadge verdict={cell.evaluation.verdict} /> : null}
      </div>
      {answerExcerpt ? (
        <p className="mt-3 line-clamp-3 text-ink">{answerExcerpt}</p>
      ) : cell.status === "failed" && providerMessage ? (
        <p className="mt-3 text-red-700">{providerMessage}</p>
      ) : (
        <p className="mt-3 text-subtle">{t("matrix.cell.noExcerpt")}</p>
      )}
      {rationale ? <p className="mt-2 line-clamp-2 text-xs text-subtle">{rationale}</p> : null}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs text-subtle">
          {t("matrix.cell.sources", { count: cell.sources_count ?? 0 })}
        </span>
        <Button
          type="button"
          variant="ghost"
          className="min-h-8 px-2"
          aria-label={t("matrix.details.open", {
            query: row.query_text,
            target: column.label,
          })}
          onClick={() => onSelect({ row, column, cell })}
        >
          <ChevronDown className="size-4" aria-hidden="true" />
          {t("matrix.cell.details")}
        </Button>
      </div>
    </div>
  );
}

function CellDetails({
  selection,
  onClose,
}: {
  selection: SelectedCell | null;
  onClose: () => void;
}) {
  const { t } = useTranslation("results");
  if (!selection) {
    return (
      <aside className="rounded-md border border-border bg-white p-4 text-sm text-subtle">
        <h3 className="font-semibold text-ink">{t("matrix.details.title")}</h3>
        <p className="mt-2">{t("matrix.details.placeholder")}</p>
      </aside>
    );
  }

  const { row, column, cell } = selection;
  const safeAnswer = safeText(cell.answer_excerpt, "");
  const safeRationale = safeText(cell.evaluation?.rationale, "");
  const concepts = cell.concepts ?? [];
  const competitors = cell.competitor_candidates ?? [];

  return (
    <aside
      aria-live="polite"
      className="rounded-md border border-border bg-white p-4 text-sm"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-ink">{t("matrix.details.title")}</h3>
          <p className="mt-1 text-subtle">{safeText(row.query_text, t("matrix.unknown"))}</p>
        </div>
        <Button
          type="button"
          variant="ghost"
          className="min-h-8 px-2"
          aria-label={t("matrix.details.close")}
          onClick={onClose}
        >
          <X className="size-4" aria-hidden="true" />
        </Button>
      </div>

      <dl className="mt-4 grid gap-3 md:grid-cols-3">
        <div>
          <dt className="text-xs font-semibold uppercase text-subtle">
            {t("matrix.details.target")}
          </dt>
          <dd className="mt-1 font-medium text-ink">{safeText(column.label, "N/A")}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase text-subtle">
            {t("matrix.details.level")}
          </dt>
          <dd className="mt-1 font-medium text-ink">{column.level}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase text-subtle">
            {t("matrix.details.status")}
          </dt>
          <dd className="mt-1">
            <MatrixStatusBadge status={cell.status} />
          </dd>
        </div>
      </dl>

      <div className="mt-4 rounded-md border border-border bg-muted p-3">
        <p className="text-xs font-semibold uppercase text-subtle">
          {t("matrix.details.safeAnswer")}
        </p>
        <p className="mt-2 whitespace-pre-wrap text-ink">
          {safeAnswer || t("matrix.details.excerptOnly")}
        </p>
      </div>

      {cell.evaluation ? (
        <div className="mt-4 rounded-md border border-border p-3">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xs font-semibold uppercase text-subtle">
              {t("matrix.details.evaluation")}
            </p>
            <VerdictBadge verdict={cell.evaluation.verdict} />
          </div>
          {safeRationale ? <p className="mt-2 text-ink">{safeRationale}</p> : null}
          {cell.evaluation.confidence !== null && cell.evaluation.confidence !== undefined ? (
            <p className="mt-2 text-xs text-subtle">
              {t("matrix.details.confidence", { value: cell.evaluation.confidence })}
            </p>
          ) : null}
        </div>
      ) : null}

      {cell.provider_error ? (
        <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-3">
          <p className="font-semibold text-red-900">{t("matrix.details.diagnostic")}</p>
          <ProviderIssueText diagnostic={cell.provider_error} />
        </div>
      ) : null}

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div className="rounded-md border border-border p-3">
          <p className="text-xs font-semibold uppercase text-subtle">
            {t("matrix.details.sources")}
          </p>
          <p className="mt-1 text-lg font-semibold text-ink">{cell.sources_count ?? 0}</p>
        </div>
        <div className="rounded-md border border-border p-3">
          <p className="text-xs font-semibold uppercase text-subtle">
            {t("matrix.details.concepts")}
          </p>
          <p className="mt-1 text-sm text-ink">
            {concepts.length > 0
              ? concepts.map((concept) => safeText(concept.text, "")).filter(Boolean).join(", ")
              : t("matrix.details.none")}
          </p>
        </div>
        <div className="rounded-md border border-border p-3">
          <p className="text-xs font-semibold uppercase text-subtle">
            {t("matrix.details.competitors")}
          </p>
          <p className="mt-1 text-sm text-ink">
            {competitors.length > 0
              ? competitors
                  .map((competitor) => safeText(competitor.name, ""))
                  .filter(Boolean)
                  .join(", ")
              : t("matrix.details.none")}
          </p>
        </div>
      </div>
    </aside>
  );
}

function MatrixFiltersPanel({
  matrix,
  filters,
  onChange,
  onClear,
}: {
  matrix: AnswerMatrixResponse;
  filters: MatrixFilters;
  onChange: (filters: MatrixFilters) => void;
  onClear: () => void;
}) {
  const { t } = useTranslation(["results", "audits"]);
  const aiFamilies = uniqueValues(matrix.columns.map((column) => column.ai_family));
  const models = uniqueValues(matrix.columns.map(columnModelValue));
  const queryTypes = uniqueValues(matrix.rows.map((row) => row.query_type ?? "unknown"));

  return (
    <div className="rounded-md border border-border bg-white p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end">
        <div className="grid flex-1 gap-3 sm:grid-cols-2 xl:grid-cols-6">
          <FieldSelect
            label={t("results:matrix.filters.level")}
            value={filters.level}
            options={[
              { value: "all", label: t("results:matrix.filters.allLevels") },
              { value: "L1", label: "L1" },
              { value: "L2", label: "L2" },
            ]}
            onChange={(level) => onChange({ ...filters, level })}
          />
          <FieldSelect
            label={t("results:matrix.filters.aiFamily")}
            value={filters.aiFamily}
            options={[
              { value: "all", label: t("results:matrix.filters.allFamilies") },
              ...aiFamilies.map((family) => ({ value: family, label: optionLabel(family) })),
            ]}
            onChange={(aiFamily) => onChange({ ...filters, aiFamily })}
          />
          <FieldSelect
            label={t("results:matrix.filters.model")}
            value={filters.model}
            options={[
              { value: "all", label: t("results:matrix.filters.allModels") },
              ...models.map((model) => ({ value: model, label: optionLabel(model) })),
            ]}
            onChange={(model) => onChange({ ...filters, model })}
          />
          <FieldSelect
            label={t("results:matrix.filters.verdict")}
            value={filters.verdict}
            options={[
              { value: "all", label: t("results:matrix.filters.allVerdicts") },
              ...verdicts.map((verdict) => ({
                value: verdict,
                label: t(`results:matrix.verdict.${verdict}`),
              })),
            ]}
            onChange={(verdict) => onChange({ ...filters, verdict })}
          />
          <FieldSelect
            label={t("results:matrix.filters.queryType")}
            value={filters.queryType}
            options={[
              { value: "all", label: t("results:matrix.filters.allQueryTypes") },
              ...queryTypes.map((type) => ({
                value: type,
                label: t(`audits:queryTypes.${type}`, { defaultValue: type }),
              })),
            ]}
            onChange={(queryType) => onChange({ ...filters, queryType })}
          />
          <FieldSelect
            label={t("results:matrix.filters.status")}
            value={filters.status}
            options={[
              { value: "all", label: t("results:matrix.filters.allStatuses") },
              ...cellStatuses.map((status) => ({
                value: status,
                label: t(`results:matrix.status.${status}`),
              })),
            ]}
            onChange={(status) => onChange({ ...filters, status })}
          />
        </div>
        <Button type="button" variant="secondary" onClick={onClear}>
          {t("results:matrix.filters.clear")}
        </Button>
      </div>
    </div>
  );
}

function AnswerMatrixGrid({
  matrix,
  filters,
  onSelectCell,
}: {
  matrix: AnswerMatrixResponse;
  filters: MatrixFilters;
  onSelectCell: (selection: SelectedCell) => void;
}) {
  const { t } = useTranslation("results");
  const columns = useMemo(() => visibleColumns(matrix.columns, filters), [matrix.columns, filters]);
  const rows = useMemo(
    () => visibleRows(matrix.rows, columns, filters),
    [columns, filters, matrix.rows],
  );

  if (columns.length === 0 || rows.length === 0) {
    return (
      <div className="rounded-md border border-border bg-white p-4 text-sm text-subtle">
        {t("matrix.empty.filtered")}
      </div>
    );
  }

  return (
    <div
      className="overflow-x-auto rounded-md border border-border bg-white"
      data-testid="answer-matrix-scroll"
    >
      <table className="min-w-[900px] border-separate border-spacing-0 text-left text-sm">
        <thead className="bg-muted text-xs uppercase text-subtle">
          <tr>
            <th className="sticky left-0 z-10 w-72 border-b border-border bg-muted px-4 py-3 font-semibold">
              {t("matrix.question")}
            </th>
            {columns.map((column) => (
              <th
                key={column.target_id}
                className="min-w-72 border-b border-l border-border px-4 py-3 align-top font-semibold"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-ink normal-case">{safeText(column.label, "N/A")}</span>
                  <span className="rounded-full bg-white px-2 py-0.5 text-xs text-subtle">
                    {column.level}
                  </span>
                  {column.gateway_l2_experimental ? (
                    <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-700">
                      {t("matrix.openRouterExperimental")}
                    </span>
                  ) : null}
                </div>
                <p className="mt-1 text-xs font-normal normal-case text-subtle">
                  {optionLabel(column.model_id ?? column.execution_provider)}
                </p>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const cells = rowCellsByTarget(row);
            return (
              <tr key={row.query_id} className="align-top">
                <th className="sticky left-0 z-10 w-72 border-b border-border bg-white px-4 py-4 font-medium text-ink">
                  <p className="max-w-64 whitespace-normal break-words">{safeText(row.query_text)}</p>
                  <p className="mt-2 text-xs font-normal text-subtle">
                    {t(`audits:queryTypes.${row.query_type ?? "unknown"}`, {
                      defaultValue: row.query_type ?? "unknown",
                    })}
                  </p>
                </th>
                {columns.map((column) => {
                  const cell = cells.get(column.target_id);
                  const showCell = cellPassesFilters(cell, filters);
                  return (
                    <td
                      key={`${row.query_id}-${column.target_id}`}
                      className="border-b border-l border-border p-3 align-top"
                    >
                      {cell && showCell ? (
                        <MatrixCell
                          cell={cell}
                          row={row}
                          column={column}
                          onSelect={onSelectCell}
                        />
                      ) : (
                        <MissingCell />
                      )}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function AnswerMatrixShell({
  auditId,
  auditStatus,
}: {
  auditId: number;
  auditStatus?: AuditStatus | null;
}) {
  const { t } = useTranslation("results");
  const matrix = useAuditAnswerMatrix(auditId);
  const [filters, setFilters] = useState<MatrixFilters>(defaultFilters);
  const [selectedCell, setSelectedCell] = useState<SelectedCell | null>(null);

  if (matrix.isLoading) {
    return (
      <section
        className="mx-5 mt-5 rounded-md border border-border bg-muted px-4 py-3 text-sm text-subtle"
        role="status"
      >
        {t("matrix.loading")}
      </section>
    );
  }

  if (matrix.isError) {
    return (
      <section className="mx-5 mt-5 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900">
        <div className="flex items-center gap-2 font-semibold">
          <AlertTriangle className="size-4" aria-hidden="true" />
          {t("matrix.errorTitle")}
        </div>
        <p className="mt-2">{t("matrix.errorBody")}</p>
      </section>
    );
  }

  const data = matrix.data;
  if (!data) {
    return null;
  }

  const hasData = matrixHasData(data);
  const showPartialWarning = auditStatus === "partial";
  const showFailedWarning = auditStatus === "failed";
  const showCancelledWarning = auditStatus === "cancelled";
  const showRunningState = auditStatus === "running";
  const showExperimentalNotice = hasOpenRouterExperimentalL2(data.columns);

  return (
    <section className="mx-5 mt-5 space-y-4 rounded-md border border-border bg-muted/40 p-4">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase text-subtle">
            {t("matrix.eyebrow")}
          </p>
          <h2 className="mt-1 text-lg font-semibold text-ink">{t("matrix.title")}</h2>
          <p className="mt-1 text-sm text-subtle">
            {t("matrix.subtitle", {
              rows: data.rows.length,
              columns: data.columns.length,
            })}
          </p>
        </div>
        <div className="rounded-md border border-border bg-white px-3 py-2 text-sm text-subtle">
          {t("matrix.endpointLabel")}:{" "}
          <span className="font-medium text-ink">answer-matrix</span>
        </div>
      </div>

      {showRunningState ? (
        <div className="rounded-md border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">
          {t("matrix.states.running")}
        </div>
      ) : null}
      {showPartialWarning ? (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {t("matrix.states.partial")}
        </div>
      ) : null}
      {showFailedWarning ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900">
          {t("matrix.states.failed")}
        </div>
      ) : null}
      {showCancelledWarning ? (
        <div className="rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900">
          {t("matrix.states.cancelled")}
        </div>
      ) : null}
      {showExperimentalNotice ? (
        <div className="rounded-md border border-amber-200 bg-white px-4 py-3 text-sm text-amber-900">
          {t("matrix.openRouterExperimentalNotice")}
        </div>
      ) : null}

      <ProviderDiagnostics diagnostics={data.provider_diagnostics} compact />
      {data.provider_diagnostics && data.provider_diagnostics.length > 0 ? null : (
        <div className="rounded-md border border-border bg-white px-4 py-3 text-sm text-subtle">
          {t("matrix.diagnosticsPlaceholder")}
        </div>
      )}

      <MatrixFiltersPanel
        matrix={data}
        filters={filters}
        onChange={(nextFilters) => {
          setFilters(nextFilters);
          setSelectedCell(null);
        }}
        onClear={() => {
          setFilters(defaultFilters);
          setSelectedCell(null);
        }}
      />

      {!hasData ? (
        <div className="rounded-md border border-border bg-white p-4 text-sm text-subtle">
          {t("matrix.empty.noData")}
        </div>
      ) : (
        <AnswerMatrixGrid
          matrix={data}
          filters={filters}
          onSelectCell={setSelectedCell}
        />
      )}

      <CellDetails selection={selectedCell} onClose={() => setSelectedCell(null)} />
    </section>
  );
}
