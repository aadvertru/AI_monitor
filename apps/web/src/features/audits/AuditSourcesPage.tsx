import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { getAuditDetail, getAuditSourceDomains } from "../../lib/api/client";
import type { SourceDomainGroup, SourceDomainUrl } from "../../lib/api/types";
import { AuditBreadcrumbs } from "./AuditBreadcrumbs";
import { AuditViewTabs } from "./AuditViewTabs";

function joinValues(values: string[]) {
  return values.length > 0 ? values.join(", ") : "N/A";
}

function evidenceTitle(source: SourceDomainUrl, fallback: string) {
  return source.title ?? source.normalized_url ?? source.url ?? fallback;
}

function evidenceMeta(source: SourceDomainUrl) {
  return [source.level, source.execution_provider, source.model_id].filter(Boolean).join(" · ");
}

function domainKey(domain: SourceDomainGroup) {
  return domain.domain;
}

export function AuditSourcesPage() {
  const { t } = useTranslation("results");
  const params = useParams();
  const auditId = Number(params.auditId);
  const isValidAuditId = Number.isInteger(auditId) && auditId > 0;
  const [expandedDomains, setExpandedDomains] = useState<Set<string>>(new Set());

  const detail = useQuery({
    queryKey: ["audit", auditId],
    queryFn: () => getAuditDetail(auditId),
    enabled: isValidAuditId,
    retry: false,
  });
  const sourceDomains = useQuery({
    queryKey: ["audit", auditId, "source-domains"],
    queryFn: () => getAuditSourceDomains(auditId),
    enabled: isValidAuditId,
    retry: false,
  });

  if (detail.isLoading || sourceDomains.isLoading) {
    return (
      <section
        className="rounded-md border border-border bg-surface px-5 py-10 text-sm text-subtle shadow-panel"
        role="status"
      >
        {t("loadingSources")}
      </section>
    );
  }

  if (
    detail.isError ||
    sourceDomains.isError ||
    !detail.data ||
    !sourceDomains.data ||
    !isValidAuditId
  ) {
    return (
      <section className="rounded-md border border-border bg-surface p-5 shadow-panel">
        <div className="flex items-center gap-2 text-sm text-red-700">
          <AlertTriangle className="size-4" aria-hidden="true" />
          {t("loadSourcesError")}
        </div>
      </section>
    );
  }

  const domains = sourceDomains.data.domains;

  function toggleDomain(domain: string) {
    setExpandedDomains((current) => {
      const next = new Set(current);
      if (next.has(domain)) {
        next.delete(domain);
      } else {
        next.add(domain);
      }
      return next;
    });
  }

  return (
    <section className="rounded-md border border-border bg-surface shadow-panel">
      <div className="flex flex-col gap-3 border-b border-border px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <AuditBreadcrumbs
            auditId={auditId}
            auditNumber={detail.data.audit_number}
            current={t("sources")}
          />
          <h1 className="text-xl font-semibold text-ink">{t("sourceIntelligence")}</h1>
          <p className="mt-1 text-sm text-subtle">
            {t("auditSources", {
              count: domains.length,
              number: detail.data.audit_number,
            })}
          </p>
        </div>
        <Button asChild variant="ghost">
          <Link to={`/audits/${auditId}`}>
            <ArrowLeft className="size-4" aria-hidden="true" />
            {t("backToDetail")}
          </Link>
        </Button>
      </div>

      <AuditViewTabs auditId={auditId} active="sources" />

      {sourceDomains.data.warnings.length > 0 ? (
        <div className="border-b border-border px-5 py-3 text-sm text-amber-700">
          {sourceDomains.data.warnings.join(" ")}
        </div>
      ) : null}

      {domains.length === 0 ? (
        <div className="px-5 py-10">
          <p className="text-sm font-medium text-ink">{t("empty.sourcesTitle")}</p>
          <p className="mt-1 text-sm text-subtle">{t("empty.sourcesBody")}</p>
        </div>
      ) : null}

      {domains.length > 0 ? (
        <div className="divide-y divide-border">
          {domains.map((domain) => {
            const isExpanded = expandedDomains.has(domainKey(domain));
            return (
              <article key={domainKey(domain)} className="px-5 py-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0">
                    <h2 className="break-words text-base font-semibold text-ink">{domain.domain}</h2>
                    <p className="mt-1 text-sm text-subtle">
                      {domain.source_count} citations · {domain.unique_url_count} URLs ·{" "}
                      {domain.query_count} queries
                    </p>
                    <p className="mt-1 break-words text-xs text-subtle">
                      {joinValues(domain.providers)} · {joinValues(domain.levels)} ·{" "}
                      {joinValues(domain.models)}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => toggleDomain(domainKey(domain))}
                    aria-expanded={isExpanded}
                  >
                    {isExpanded ? (
                      <ChevronUp className="size-4" aria-hidden="true" />
                    ) : (
                      <ChevronDown className="size-4" aria-hidden="true" />
                    )}
                    {t("table.details")}
                  </Button>
                </div>

                {isExpanded ? (
                  <div className="mt-4 space-y-3">
                    {domain.urls.map((source) => (
                      <SourceEvidenceRow
                        key={`${source.normalized_url}-${source.query_id ?? "query"}`}
                        source={source}
                      />
                    ))}
                  </div>
                ) : null}
              </article>
            );
          })}
        </div>
      ) : null}
    </section>
  );
}

function SourceEvidenceRow({ source }: { source: SourceDomainUrl }) {
  const { t } = useTranslation("results");
  const meta = evidenceMeta(source);

  return (
    <div className="rounded-md border border-border bg-muted/40 p-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="break-words text-sm font-medium text-ink">
            {evidenceTitle(source, t("sections.untitledSource"))}
          </p>
          {source.snippet ? (
            <p className="mt-1 line-clamp-3 break-words text-sm text-subtle">{source.snippet}</p>
          ) : null}
          {source.query_text ? (
            <p className="mt-2 break-words text-xs text-subtle">{source.query_text}</p>
          ) : null}
          {meta ? <p className="mt-1 break-words text-xs text-subtle">{meta}</p> : null}
        </div>
        <a
          className="inline-flex shrink-0 items-center gap-1 break-all text-sm font-medium text-brand-700 hover:underline"
          href={source.normalized_url}
          rel="noopener noreferrer"
          target="_blank"
        >
          {source.normalized_url}
          <ExternalLink className="size-3" aria-hidden="true" />
        </a>
      </div>
    </div>
  );
}
