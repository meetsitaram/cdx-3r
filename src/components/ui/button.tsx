import { cn } from "@/lib/utils";
import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "ghost" | "danger";

export function Button({
  className,
  variant = "primary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      className={cn(
        "inline-flex min-h-11 items-center justify-center gap-2 rounded-sm px-4 text-sm font-medium transition-opacity duration-150 disabled:opacity-40",
        variant === "primary" && "bg-fg text-bg hover:opacity-90",
        variant === "ghost" && "border border-border bg-transparent text-fg hover:bg-elevated",
        variant === "danger" && "bg-danger text-danger-fg hover:opacity-90",
        className,
      )}
      {...props}
    />
  );
}
