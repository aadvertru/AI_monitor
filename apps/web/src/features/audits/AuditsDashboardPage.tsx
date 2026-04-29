import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Plus } from "lucide-react";

import { Button } from "../../components/ui/Button";
import { listAudits } from "../../lib/api/client";

export function AuditsDashboardPage() {
  const audits = useQuery({
    queryKey: ["audits"],
    queryFn: listAudits,
  });

  return (
    <section className="rounded-md border border-border bg-surface shadow-panel">
      <div className="flex flex-col gap-3 border-b border-border px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-ink">Audits</h1>
          <p className="text-sm text-subtle">SCDL brand visibility checks</p>
        </div>
        <Button type="button" variant="secondary">
          <Plus className="size-4" aria-hidden="true" />
          New audit
        </Button>
      </div>

      {audits.isLoading ? (
        <div className="px-5 py-10 text-sm text-subtle">Loading audits...</div>
      ) : null}

      {audits.isError ? (
        <div className="flex items-center gap-2 px-5 py-10 text-sm text-red-700">
          <AlertTriangle className="size-4" aria-hidden="true" />
          Unable to load audits.
        </div>
      ) : null}

      {audits.data && audits.data.length === 0 ? (
        <div className="px-5 py-10">
          <p className="text-sm font-medium text-ink">No audits yet</p>
          <p className="mt-1 text-sm text-subtle">Create an audit to track AI visibility.</p>
        </div>
      ) : null}

      {audits.data && audits.data.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-border text-sm">
            <thead className="bg-muted text-left text-xs uppercase text-subtle">
              <tr>
                <th className="px-5 py-3 font-semibold">Brand</th>
                <th className="px-5 py-3 font-semibold">Status</th>
                <th className="px-5 py-3 font-semibold">Level</th>
                <th className="px-5 py-3 font-semibold">Providers</th>
                <th className="px-5 py-3 font-semibold">Runs</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {audits.data.map((audit) => (
                <tr key={audit.audit_id}>
                  <td className="px-5 py-3">
                    <span className="font-medium text-ink">{audit.brand_name}</span>
                    {audit.brand_domain ? (
                      <span className="ml-2 text-subtle">{audit.brand_domain}</span>
                    ) : null}
                  </td>
                  <td className="px-5 py-3 text-subtle">{audit.status}</td>
                  <td className="px-5 py-3 text-subtle">{audit.scdl_level}</td>
                  <td className="px-5 py-3 text-subtle">{audit.providers.join(", ")}</td>
                  <td className="px-5 py-3 text-subtle">{audit.runs_per_query}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
