"use client";

import {
  DndContext,
  PointerSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { Badge } from "@/features/ui";
import { cn } from "@/lib/cn";
import LeadCard from "./lead-card";
import type { Lead } from "./types";
import {
  EDITABLE_STATUSES,
  boardColumns,
  getStatusMeta,
  groupLeadsByStatus,
} from "./lead-status";
import { useBoardLeads } from "./use-board-leads";
import { moveLeadAction } from "./actions";

/**
 * Interactive kanban: leads grouped into one column per board status, with
 * drag & drop between columns (@dnd-kit/core). Moves are optimistic — the card
 * jumps on drop and reverts with an inline error if the backend rejects the
 * change (state machine in use-board-leads.ts). Columns for engine-owned
 * statuses (unreachable/failed) render but are not drop targets: the API would
 * 400 on them anyway.
 *
 * The horizontal overflow-x-auto scroll is intentional and must stay: a
 * half-visible card is the affordance that there are more columns to the right.
 */
export default function ClientBoardView({ leads: serverLeads }: { leads: Lead[] }) {
  const { leads, moveLead, error } = useBoardLeads(serverLeads, moveLeadAction);
  // The 8px activation distance keeps plain clicks navigating to the lead
  // detail (the card is a <Link>); only a real drag starts a move.
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  );

  if (leads.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border p-12 text-center text-muted-foreground">
        No hay clientes potenciales en el tablero. Usa el botón «Nuevo cliente
        potencial» para comenzar.
      </div>
    );
  }

  const columns = boardColumns(leads);
  const groups = groupLeadsByStatus(leads);

  function handleDragEnd(event: DragEndEvent) {
    const target = event.over?.id;
    if (typeof target !== "string") return;
    void moveLead(String(event.active.id), target);
  }

  return (
    <div className="flex flex-col gap-3">
      {error && (
        <p
          role="alert"
          className="rounded-lg border border-danger-500/30 bg-danger-500/10 px-3 py-2 text-sm text-danger-700"
        >
          {error}
        </p>
      )}

      {/* Stable id: dnd-kit derives its aria-describedby ("DndDescribedBy-N")
          from a global counter, which drifts between the SSR pass and the
          client and triggers a hydration mismatch without it. */}
      <DndContext id="client-board" sensors={sensors} onDragEnd={handleDragEnd}>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {columns.map((status) => (
            <BoardColumn
              key={status}
              status={status}
              leads={groups.get(status) ?? []}
            />
          ))}
        </div>
      </DndContext>
    </div>
  );
}

function BoardColumn({ status, leads }: { status: string; leads: Lead[] }) {
  const droppable = EDITABLE_STATUSES.includes(status);
  const { setNodeRef, isOver } = useDroppable({ id: status, disabled: !droppable });
  const meta = getStatusMeta(status);

  return (
    <section
      ref={setNodeRef}
      className={cn(
        "flex w-72 shrink-0 flex-col gap-3 rounded-xl bg-muted/40 p-3 transition-colors",
        isOver && droppable && "bg-brand-50 ring-2 ring-brand-500/40",
      )}
    >
      <header className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <Badge tone={meta.tone}>{meta.label}</Badge>
        </div>
        <span className="text-xs font-medium text-muted-foreground">
          {leads.length}
        </span>
      </header>

      <div className="flex flex-col gap-3">
        {leads.map((lead) => (
          <DraggableLeadCard key={lead.id} lead={lead} />
        ))}
        {leads.length === 0 && (
          <p className="px-1 py-6 text-center text-xs text-muted-foreground">
            Sin leads
          </p>
        )}
      </div>
    </section>
  );
}

function DraggableLeadCard({ lead }: { lead: Lead }) {
  const { setNodeRef, listeners, attributes, transform, isDragging } = useDraggable({
    id: lead.id,
  });

  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      // touch-none: the PointerSensor needs the browser not to hijack the
      // gesture for scrolling while a card is being dragged.
      className={cn(
        "touch-none cursor-grab active:cursor-grabbing",
        isDragging && "relative z-10 opacity-90",
      )}
      style={
        transform
          ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` }
          : undefined
      }
    >
      <LeadCard lead={lead} />
    </div>
  );
}
