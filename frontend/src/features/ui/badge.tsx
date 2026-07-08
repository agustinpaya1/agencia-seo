import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export type BadgeTone =
  | "neutral"
  | "brand"
  | "success"
  | "warning"
  | "danger";

const base =
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 " +
  "text-xs font-semibold whitespace-nowrap";

// tone -> full class list. Coloured tones can't ride the semantic surface
// tokens, so each carries an explicit light value plus a `dark:` override.
// The app defaults to the light theme, so the light halves are what normally
// renders; the `dark:` halves only activate if a future toggle adds the .dark
// class (globals.css keeps that infrastructure). Centralised here so consuming
// components (status badges across leads/presupuestos/proyectos) never repeat
// the split.
const toneClasses: Record<BadgeTone, string> = {
  neutral: "border-border bg-muted text-muted-foreground",
  brand:
    "border-brand-500/20 bg-brand-500/10 text-brand-700 " +
    "dark:border-brand-400/25 dark:bg-brand-500/15 dark:text-brand-300",
  success:
    "border-success-500/20 bg-success-500/10 text-success-700 " +
    "dark:border-success-400/25 dark:bg-success-500/15 dark:text-success-300",
  warning:
    "border-warning-500/20 bg-warning-500/10 text-warning-700 " +
    "dark:border-warning-400/25 dark:bg-warning-500/15 dark:text-warning-300",
  danger:
    "border-danger-500/20 bg-danger-500/10 text-danger-700 " +
    "dark:border-danger-400/25 dark:bg-danger-500/15 dark:text-danger-300",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
}

export function Badge({ tone = "neutral", className, ...props }: BadgeProps) {
  return <span className={cn(base, toneClasses[tone], className)} {...props} />;
}
