import { Navigate, useParams } from "react-router-dom";

export function AuditSummaryRedirect() {
  const params = useParams();

  return <Navigate to={`/audits/${params.auditId}`} replace />;
}
