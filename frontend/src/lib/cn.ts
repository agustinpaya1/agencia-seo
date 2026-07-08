export type ClassValue = string | number | false | null | undefined;

/**
 * Minimal className joiner. Filters out falsy values so conditional classes can
 * be written inline (`cn("base", isActive && "active")`).
 *
 * Deliberately not `clsx` + `tailwind-merge`: the design-system primitives use
 * non-overlapping variant maps (see button.tsx / badge.tsx), so there are no
 * conflicting Tailwind classes to dedupe and no extra dependency is warranted.
 * If we ever need last-wins merging of conflicting utilities, revisit this.
 */
export function cn(...classes: ClassValue[]): string {
  return classes.filter(Boolean).join(" ");
}
