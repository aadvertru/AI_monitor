import { AlertTriangle } from "lucide-react";

import type { ProviderDiagnostic } from "../../lib/api/types";

const unsafePattern =
  /api_key|authorization|headers|raw_response|raw_prompt|prompt|stack_trace|traceback|openai_api_key|anthropic_api_key|sk-/i;

function safeText(value: unknown, fallback = "Provider issue details are unavailable.") {
  if (typeof value !== "string" || unsafePattern.test(value)) {
    return fallback;
  }
  return value;
}

function dedupeDiagnostics(diagnostics: ProviderDiagnostic[]) {
  const grouped = new Map<string, ProviderDiagnostic & { count: number }>();
  for (const diagnostic of diagnostics) {
    const key = [
      diagnostic.code,
      diagnostic.provider,
      diagnostic.level ?? "",
      diagnostic.model ?? "",
      diagnostic.message,
    ].join("|");
    const existing = grouped.get(key);
    if (existing) {
      existing.count += 1;
    } else {
      grouped.set(key, { ...diagnostic, count: 1 });
    }
  }
  return Array.from(grouped.values());
}

export function ProviderDiagnostics({
  diagnostics,
  compact = false,
}: {
  diagnostics?: ProviderDiagnostic[] | null;
  compact?: boolean;
}) {
  const safeDiagnostics = dedupeDiagnostics(diagnostics ?? []);

  if (safeDiagnostics.length === 0) {
    return null;
  }

  return (
    <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900">
      <div className="flex items-center gap-2 font-semibold">
        <AlertTriangle className="size-4" aria-hidden="true" />
        Provider issue
      </div>
      <ul className={compact ? "mt-2 space-y-2" : "mt-3 space-y-3"}>
        {safeDiagnostics.map((diagnostic) => (
          <li
            key={`${diagnostic.code}-${diagnostic.provider}-${diagnostic.level ?? ""}-${diagnostic.model ?? ""}`}
          >
            <p>{safeText(diagnostic.message)}</p>
            <p className="mt-1 text-xs text-red-800">
              {safeText(diagnostic.provider, "provider")}
              {diagnostic.level ? ` - ${safeText(diagnostic.level)}` : ""}
              {diagnostic.model ? ` - ${safeText(diagnostic.model)}` : ""}
              {diagnostic.retryable ? " - retryable" : ""}
              {diagnostic.count > 1 ? ` - ${diagnostic.count} runs` : ""}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ProviderIssueText({
  diagnostic,
}: {
  diagnostic?: ProviderDiagnostic | null;
}) {
  if (!diagnostic) {
    return null;
  }
  return (
    <p className="mt-1 text-xs text-red-700">
      Provider issue: {safeText(diagnostic.message)}
    </p>
  );
}
