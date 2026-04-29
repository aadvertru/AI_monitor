import { type InputHTMLAttributes, forwardRef } from "react";
import { clsx } from "clsx";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={clsx(
        "h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink outline-none transition-colors placeholder:text-slate-400 focus:border-brand-600 focus:ring-2 focus:ring-brand-100",
        className,
      )}
      {...props}
    />
  ),
);

Input.displayName = "Input";
