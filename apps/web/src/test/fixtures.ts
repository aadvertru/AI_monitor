import type { AuditListItem, CurrentUser } from "../lib/api/types";

export const currentUserFixture: CurrentUser = {
  id: 1,
  email: "user@example.com",
  role: "user",
};

export const auditListFixture: AuditListItem[] = [
  {
    audit_id: 42,
    brand_name: "Acme AI",
    brand_domain: "acme.example",
    status: "created",
    scdl_level: "L1",
    providers: ["mock"],
    runs_per_query: 1,
    created_at: "2026-04-29T09:30:00Z",
    updated_at: "2026-04-29T09:30:00Z",
  },
];
