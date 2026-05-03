import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Plus, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import {
  archiveAudit,
  deleteArchivedAudit,
  listAudits,
  restoreAudit,
} from "../../lib/api/client";
import type { AuditListItem } from "../../lib/api/types";
import {
  archiveConfirmationMessage,
  deleteConfirmationMessage,
} from "./auditActions";
import { AuditRowActions } from "./AuditRowActions";
import { AuditStatusBadge } from "./AuditStatusBadge";

function formatTimestamp(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function matchesSearch(audit: AuditListItem, query: string) {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) {
    return true;
  }

  return [
    audit.audit_number.toString(),
    audit.brand_name,
    audit.brand_domain ?? "",
    audit.status,
    audit.scdl_level,
    audit.providers.join(" "),
  ]
    .some((value) => value.toLowerCase().includes(normalizedQuery));
}

export function AuditsDashboardPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const audits = useQuery({
    queryKey: ["audits", showArchived ? "archived" : "active"],
    queryFn: () => listAudits({ archived: showArchived }),
  });
  const invalidateAuditLists = () => {
    void queryClient.invalidateQueries({ queryKey: ["audits"] });
  };
  const archiveAuditMutation = useMutation({
    mutationFn: archiveAudit,
    onSuccess: invalidateAuditLists,
  });
  const restoreAuditMutation = useMutation({
    mutationFn: restoreAudit,
    onSuccess: invalidateAuditLists,
  });
  const deleteAuditMutation = useMutation({
    mutationFn: deleteArchivedAudit,
    onSuccess: invalidateAuditLists,
  });
  const filteredAudits = useMemo(
    () => audits.data?.filter((audit) => matchesSearch(audit, search)) ?? [],
    [audits.data, search],
  );

  return (
    <section className="rounded-md border border-border bg-surface shadow-panel">
      <div className="flex flex-col gap-3 border-b border-border px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-ink">Audits</h1>
          <p className="text-sm text-subtle">SCDL brand visibility checks</p>
        </div>
        <Button asChild variant="secondary">
          <Link to="/audits/new">
            <Plus className="size-4" aria-hidden="true" />
            New audit
          </Link>
        </Button>
      </div>

      <div className="flex gap-2 border-b border-border px-5 py-3">
        <Button
          type="button"
          variant={showArchived ? "ghost" : "secondary"}
          onClick={() => setShowArchived(false)}
        >
          Active
        </Button>
        <Button
          type="button"
          variant={showArchived ? "secondary" : "ghost"}
          onClick={() => setShowArchived(true)}
        >
          Archived
        </Button>
      </div>

      {audits.data && audits.data.length > 0 ? (
        <div className="border-b border-border px-5 py-3">
          <label className="relative block max-w-sm">
            <span className="sr-only">Search audits</span>
            <Search
              className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400"
              aria-hidden="true"
            />
            <Input
              className="pl-9"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search audits"
            />
          </label>
        </div>
      ) : null}

      {audits.isLoading ? (
        <div className="px-5 py-10 text-sm text-subtle" role="status">
          Loading audits...
        </div>
      ) : null}

      {audits.isError ? (
        <div className="flex items-center gap-2 px-5 py-10 text-sm text-red-700">
          <AlertTriangle className="size-4" aria-hidden="true" />
          Unable to load audits.
        </div>
      ) : null}

      {audits.data && audits.data.length === 0 ? (
        <div className="px-5 py-10">
          <p className="text-sm font-medium text-ink">
            {showArchived ? "No archived audits" : "No audits yet"}
          </p>
          <p className="mt-1 text-sm text-subtle">
            {showArchived
              ? "Archived audits will appear here."
              : "Create an audit to track AI visibility."}
          </p>
          {!showArchived ? (
            <Button asChild className="mt-4">
              <Link to="/audits/new">
                <Plus className="size-4" aria-hidden="true" />
                New audit
              </Link>
            </Button>
          ) : null}
        </div>
      ) : null}

      {audits.data && audits.data.length > 0 && filteredAudits.length === 0 ? (
        <div className="px-5 py-10">
          <p className="text-sm font-medium text-ink">No matching audits</p>
          <p className="mt-1 text-sm text-subtle">Try a different brand, status, or provider.</p>
        </div>
      ) : null}

      {audits.data && filteredAudits.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-border text-sm">
            <thead className="bg-muted text-left text-xs uppercase text-subtle">
              <tr>
                <th className="px-5 py-3 font-semibold">Audit</th>
                <th className="px-5 py-3 font-semibold">Brand</th>
                <th className="px-5 py-3 font-semibold">Status</th>
                <th className="px-5 py-3 font-semibold">Level</th>
                <th className="px-5 py-3 font-semibold">Providers</th>
                <th className="px-5 py-3 font-semibold">Runs</th>
                <th className="px-5 py-3 font-semibold">Updated</th>
                <th className="px-5 py-3 text-right font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredAudits.map((audit) => (
                <tr key={audit.audit_id} className="hover:bg-muted/70">
                  <td className="px-5 py-3 font-mono text-xs text-subtle">
                    #{audit.audit_number}
                  </td>
                  <td className="px-5 py-3">
                    <Link
                      className="font-medium text-ink hover:text-brand-700 hover:underline"
                      to={`/audits/${audit.audit_id}`}
                    >
                      {audit.brand_name}
                    </Link>
                    {audit.brand_domain ? (
                      <span className="ml-2 text-subtle">{audit.brand_domain}</span>
                    ) : null}
                  </td>
                  <td className="px-5 py-3">
                    <AuditStatusBadge status={audit.status} />
                  </td>
                  <td className="px-5 py-3 text-subtle">{audit.scdl_level}</td>
                  <td className="px-5 py-3 text-subtle">{audit.providers.join(", ")}</td>
                  <td className="px-5 py-3 text-subtle">{audit.runs_per_query}</td>
                  <td className="px-5 py-3 text-subtle">
                    {formatTimestamp(audit.updated_at)}
                  </td>
                  <td className="px-5 py-3">
                    <AuditRowActions
                      audit={audit}
                      archived={showArchived}
                      onArchive={() => {
                        if (window.confirm(archiveConfirmationMessage)) {
                          archiveAuditMutation.mutate(audit.audit_id);
                        }
                      }}
                      onRestore={() => restoreAuditMutation.mutate(audit.audit_id)}
                      onDelete={() => {
                        if (window.confirm(deleteConfirmationMessage)) {
                          deleteAuditMutation.mutate(audit.audit_id);
                        }
                      }}
                      onRefresh={() => {
                        void audits.refetch();
                      }}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
