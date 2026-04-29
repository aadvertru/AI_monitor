import type { ReactNode } from "react";
import { ShieldCheck } from "lucide-react";

type AuthLayoutProps = {
  children: ReactNode;
  title: string;
  subtitle: string;
};

export function AuthLayout({ children, subtitle, title }: AuthLayoutProps) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <section className="w-full max-w-md rounded-md border border-border bg-surface p-6 shadow-panel">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-md bg-brand-600 text-white">
            <ShieldCheck className="size-5" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-ink">{title}</h1>
            <p className="text-sm text-subtle">{subtitle}</p>
          </div>
        </div>
        {children}
      </section>
    </main>
  );
}
