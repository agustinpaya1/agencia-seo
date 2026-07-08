"use client";

import { useState } from "react";
import Link from "next/link";
import { cn } from "@/lib/cn";

/**
 * Initials for the placeholder header: first letter of the first two words,
 * uppercased ("Circle Energy" -> "CE", "acme.com" -> "A"). Exported for tests.
 */
export function mediaCardInitials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return "?";
  return words
    .slice(0, 2)
    .map((word) => word.charAt(0).toUpperCase())
    .join("");
}

interface MediaCardProps {
  title: string;
  subtitle?: string;
  /** Pasted image URL; empty/broken -> initials placeholder on brand-100. */
  imageUrl?: string | null;
  /** Renders the card as a link when given. */
  href?: string;
  /** Active/selected: wide soft elevation + 2px brand border (via ring). */
  selected?: boolean;
  className?: string;
}

/**
 * Media Card (image-top): full-width cover image on the top half, solid body
 * below with a bold title and a slate subtitle. Pronounced radius +
 * overflow-hidden so the image follows the corner curve. The selected/active
 * treatment uses a ring instead of a real 2px border so toggling it never
 * shifts the layout. Client component only for the <img> onError fallback.
 */
export function MediaCard({
  title,
  subtitle,
  imageUrl,
  href,
  selected = false,
  className,
}: MediaCardProps) {
  const [imageFailed, setImageFailed] = useState(false);
  const showImage = Boolean(imageUrl) && !imageFailed;

  const content = (
    <>
      <div className="h-36 w-full">
        {showImage ? (
          /* Arbitrary user-pasted hosts: plain <img> — next/image would need
             every remote host whitelisted in next.config. */
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={imageUrl ?? undefined}
            alt=""
            onError={() => setImageFailed(true)}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-brand-100 dark:bg-brand-950">
            <span className="text-3xl font-bold tracking-wide text-brand-700 dark:text-brand-300">
              {mediaCardInitials(title)}
            </span>
          </div>
        )}
      </div>
      <div className="bg-card p-4">
        <h3 className="truncate font-bold text-card-foreground">{title}</h3>
        {subtitle && (
          <p className="truncate text-sm text-muted-foreground">{subtitle}</p>
        )}
      </div>
    </>
  );

  const classes = cn(
    "block overflow-hidden rounded-2xl border border-border bg-card shadow-sm transition-shadow",
    selected
      ? "ring-2 ring-brand-600 shadow-xl shadow-slate-900/10"
      : href &&
          "hover:ring-2 hover:ring-brand-600 hover:shadow-xl hover:shadow-slate-900/10",
    "focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring",
    className,
  );

  if (href) {
    return (
      <Link href={href} className={classes}>
        {content}
      </Link>
    );
  }
  return <div className={classes}>{content}</div>;
}
