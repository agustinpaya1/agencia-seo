import { Suspense } from "react";
import { LeadDetail } from "@/features/leads";

/**
 * Lead detail route. `params` is a Promise in Next.js 16 and is runtime data —
 * under Cache Components it must be read *inside* a <Suspense> boundary, not in
 * the page body (which is above the shell). So the page stays synchronous and a
 * small async child resolves the id and renders the (also dynamic) detail fetch;
 * both stream at request time behind the same fallback.
 */
export default function LeadDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return (
    <div className="px-4 py-8">
      <Suspense
        fallback={
          <div className="py-10 text-center text-muted-foreground animate-pulse">
            Cargando lead…
          </div>
        }
      >
        <ResolveLead params={params} />
      </Suspense>
    </div>
  );
}

async function ResolveLead({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <LeadDetail id={id} />;
}
