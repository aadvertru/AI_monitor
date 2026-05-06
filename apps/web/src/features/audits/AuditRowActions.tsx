import { MoreVertical } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import type { AuditListItem } from "../../lib/api/types";

type AuditRowActionsProps = {
  audit: AuditListItem;
  archived: boolean;
  onArchive: () => void;
  onDelete: () => void;
  onRefresh: () => void;
  onRestore: () => void;
};

export function AuditRowActions({
  audit,
  archived,
  onArchive,
  onDelete,
  onRefresh,
  onRestore,
}: AuditRowActionsProps) {
  const { t } = useTranslation("audits");
  const [isOpen, setIsOpen] = useState(false);
  const auditId = audit.audit_id;
  const duplicateState = {
    auditDefaults: {
      brandName: audit.brand_name,
      brandDomain: audit.brand_domain ?? "",
      providers: audit.providers,
      scdlLevel: audit.scdl_level,
    },
  };

  return (
    <div className="relative flex justify-end">
      <Button
        type="button"
        variant="ghost"
        aria-expanded={isOpen}
        aria-haspopup="menu"
        aria-label={t("rowActions.menuLabel", { id: auditId })}
        onClick={() => setIsOpen((current) => !current)}
      >
        <MoreVertical className="size-4" aria-hidden="true" />
      </Button>
      {isOpen ? (
        <div
          className="absolute right-0 top-10 z-20 w-44 rounded-md border border-border bg-white py-1 text-sm shadow-panel"
          role="menu"
        >
          {archived ? (
            <>
              <button
                className="block w-full px-3 py-2 text-left text-ink hover:bg-muted"
                role="menuitem"
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  onRestore();
                }}
              >
                {t("rowActions.restore")}
              </button>
              <button
                className="block w-full px-3 py-2 text-left text-red-700 hover:bg-red-50"
                role="menuitem"
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  onDelete();
                }}
              >
                {t("rowActions.deletePermanently")}
              </button>
            </>
          ) : (
            <>
              <Link
                className="block px-3 py-2 text-ink hover:bg-muted"
                role="menuitem"
                to={`/audits/${auditId}`}
                onClick={() => setIsOpen(false)}
              >
                {t("rowActions.open")}
              </Link>
              <button
                className="block w-full px-3 py-2 text-left text-ink hover:bg-muted"
                role="menuitem"
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  onRefresh();
                }}
              >
                {t("rowActions.refresh")}
              </button>
              <Link
                className="block px-3 py-2 text-ink hover:bg-muted"
                role="menuitem"
                to="/audits/new"
                state={duplicateState}
                onClick={() => setIsOpen(false)}
              >
                {t("rowActions.duplicate")}
              </Link>
              <button
                className="block w-full px-3 py-2 text-left text-red-700 hover:bg-red-50"
                role="menuitem"
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  onArchive();
                }}
              >
                {t("rowActions.archive")}
              </button>
            </>
          )}
        </div>
      ) : null}
    </div>
  );
}
