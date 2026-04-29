import type { ReactNode } from "react";

type FieldProps = {
  children: ReactNode;
  error?: string;
  label: string;
  htmlFor: string;
};

export function Field({ children, error, htmlFor, label }: FieldProps) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="block text-sm font-medium text-ink">
        {label}
      </label>
      {children}
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
    </div>
  );
}
