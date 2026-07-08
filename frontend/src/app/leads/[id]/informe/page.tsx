import { Suspense } from "react";
import { LeadReport } from "@/features/leads";

/**
 * Audit report route. Same Cache Components shape as the lead detail page:
 * `params` is runtime data, so it is resolved inside the <Suspense> boundary
 * by a small async child while the page body stays synchronous.
 */
export default function LeadReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return (
    <div className="px-4 py-8">
      <Suspense
        fallback={
          <div className="py-10 text-center text-muted-foreground animate-pulse">
            Cargando informe…
          </div>
        }
      >
        <ResolveReport params={params} />
      </Suspense>
    </div>
  );
}

async function ResolveReport({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <LeadReport id={id} />;
}
