import type { AuditDetail } from "../../lib/api/types";
import { auditDetailToFormDefaults } from "./auditSetupFormMapping";

export const archiveConfirmationMessage =
  "Вы уверены, что хотите архивировать этот аудит?";
export const deleteConfirmationMessage =
  "Удалить аудит навсегда? Это действие нельзя отменить.";

export function duplicateStateFromAudit(audit: AuditDetail) {
  return { auditDefaults: auditDetailToFormDefaults(audit) };
}
