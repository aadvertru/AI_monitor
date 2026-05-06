import { useMutation } from "@tanstack/react-query";
import { CheckCircle2, Loader2, ShieldAlert } from "lucide-react";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "../../components/ui/Button";
import { checkBrandDomain } from "../../lib/api/client";
import type { BrandDomainCheckResponse } from "../../lib/api/types";

type DomainAvailabilityCheckProps = {
  domain: string | undefined;
  onResultChange: (result: BrandDomainCheckResponse | null) => void;
};

const warningStatuses = new Set([
  "dns_failed",
  "http_failed",
  "timeout",
  "blocked_private_network",
  "unknown",
]);

export function DomainAvailabilityCheck({
  domain,
  onResultChange,
}: DomainAvailabilityCheckProps) {
  const { t } = useTranslation("audits");
  const normalizedDomain = domain?.trim() ?? "";
  const mutation = useMutation({
    mutationFn: checkBrandDomain,
    onSuccess: (result) => onResultChange(result),
    onError: () => onResultChange(null),
  });
  const result = mutation.data?.input === normalizedDomain ? mutation.data : null;
  const canCheck = normalizedDomain.length > 0 && !mutation.isPending;

  useEffect(() => {
    mutation.reset();
    onResultChange(null);
  }, [normalizedDomain]);

  return (
    <div className="mt-2 space-y-2 rounded-md border border-border bg-muted px-3 py-2 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-medium text-ink">{t("domainCheck.title")}</span>
        <Button
          type="button"
          variant="secondary"
          disabled={!canCheck}
          onClick={() => mutation.mutate(normalizedDomain)}
        >
          {mutation.isPending ? (
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          ) : null}
          {mutation.isPending ? t("domainCheck.checking") : t("domainCheck.check")}
        </Button>
      </div>
      {!normalizedDomain ? (
        <p className="text-subtle">{t("domainCheck.idle")}</p>
      ) : null}
      {result ? (
        <div
          className={
            result.query_generation_allowed
              ? "flex items-center gap-2 text-brand-700"
              : "flex items-center gap-2 text-amber-700"
          }
          role="status"
        >
          {result.query_generation_allowed ? (
            <CheckCircle2 className="size-4" aria-hidden="true" />
          ) : (
            <ShieldAlert className="size-4" aria-hidden="true" />
          )}
          <span>{t(`domainCheck.status.${result.status}`)}</span>
        </div>
      ) : null}
      {mutation.isError ? (
        <p className="text-amber-700">{t("domainCheck.error")}</p>
      ) : null}
      {result && warningStatuses.has(result.status) ? (
        <p className="text-amber-700">{t("domainCheck.generationBlocked")}</p>
      ) : null}
    </div>
  );
}
